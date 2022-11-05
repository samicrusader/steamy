import hashlib
import socket
import socketserver
import logging
from . import cryptography


class ConfigServerHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_address = client_address
        self.logger = logging.getLogger(f'ConfigServer/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')

        # Echo the back to the client
        version = int.from_bytes(self.request.recv(4), 'big')
        if version not in [2, 3]:
            self.logger.debug(f'Version {version} is not supported.')
            return
        self.request.send(b'\x01' + socket.inet_aton(self.client_address[0]))  # acknowledge connection
        length = int.from_bytes(self.request.recv(4), 'big')
        command = int.from_bytes(self.request.recv(1), 'big')
        if length != 1:
            message = self.request.recv((length - 1))
            print('message:', message)
        self.logger.debug(f'Client sent a version {version} command.')
        resp = '\x00\x00'
        if command == 1:  # Send PDR (Primary Description Record?), otherwise known as the first blob
            self.logger.debug('Reading PDR blob...')
            fh = open('pdr.bin', 'rb')
            resp = fh.read()
            fh.close()
            self.logger.info('Sending primary description record...')
        elif command == 2:
            """
            Send CDR (Content Description Record), otherwise known as the second blob.
            The client actually sends us it's own checksum to verify, instead of redownloading it over again on launch.
            """
            self.logger.debug('Reading CDR blob...')
            fh = open('cdr.bin', 'rb')
            cdr = fh.read()
            fh.close()
            self.logger.debug('Getting checksum of CDR blob...')
            sha1 = hashlib.sha1()
            sha1.update(cdr)
            cdr_hash = sha1.digest()
            self.logger.debug('Comparing hash of CDR blob against client\'s version...')
            if cdr_hash == version:
                self.logger.info('Client has valid content description record.')
                resp = ''
            else:
                self.logger.info('Client has invalid or newer content description record, sending new blob...')
                resp = cdr
        elif command == 4:  # Send network key
            """
            First key ends before \xbf on the second line, second key starts at \xbf on the second life, ends before
            \x02\x01\x11 on the last line.
            """
            self.logger.info('Sending network key...')
            data = b'\x30\x81\x9d\x30\x0d\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01\x05\x00\x03\x81\x8b\x00\x30\x81' \
                   b'\x87\x02\x81\x81\x00\xbf\x97\x3e\x24\xbe\xb3\x72\xc1\x2b\xea\x44\x94\x45\x0a\xfa\xee\x29\x09\x87' \
                   b'\xfe\xda\xe8\x58\x00\x57\xe4\xf1\x5b\x93\xb4\x61\x85\xb8\xda\xf2\xd9\x52\xe2\x4d\x6f\x9a\x23\x80' \
                   b'\x58\x19\x57\x86\x93\xa8\x46\xe0\xb8\xfc\xc4\x3c\x23\xe1\xf2\xbf\x49\xe8\x43\xaf\xf4\xb8\xe9\xaf' \
                   b'\x6c\x5e\x2e\x7b\x9d\xf4\x4e\x29\xe3\xc1\xc9\x3f\x16\x6e\x25\xe4\x2b\x8f\x91\x09\xbe\x8a\xd0\x34' \
                   b'\x38\x84\x5a\x3c\x19\x25\x50\x4e\xcc\x09\x0a\xab\xd4\x9a\x0f\xc6\x78\x37\x46\xff\x4e\x9e\x09\x0a' \
                   b'\xa9\x6f\x1c\x80\x09\xba\xf9\x16\x2b\x66\x71\x60\x59\x02\x01\x11'
            signature = cryptography.sign_message_rsa(cryptography.primary_key, data)
            self.request.send(len(data).to_bytes(2, 'big') + data + len(signature).to_bytes(2, 'big') + signature)
            return
        elif command == 9:  # ??
            self.logger.info('Sending response for command 9...')
            self.request.send(b'\x00\x00\x00\x01\x31\x2d\x00\x00\x00\x01\x2c')
            return
        else:
            self.logger.info(f'Unknown command {command}')
        self.request.send(len(resp).to_bytes(4, 'big') + resp)
        return


class ConfigServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = False
    logger = logging.getLogger('ConfigServer')
    logger.setLevel(logging.DEBUG)

    def serve_forever(self):
        self.logger.info('Server is listening')
        return socketserver.ThreadingTCPServer.serve_forever(self)

    def server_close(self):
        self.logger.info('Stopping server...')
        return socketserver.ThreadingTCPServer.server_close(self)

    def process_request(self, request, client_address):
        self.logger.debug(f'Connection established from {client_address}')
        return socketserver.ThreadingTCPServer.process_request(self, request, client_address)


def run(ip: str, port: int):
    address = (ip, port)  # let the kernel give us a port
    server = ConfigServer(address, ConfigServerHandler)
    server.serve_forever()