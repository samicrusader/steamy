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

        version = int.from_bytes(self.request.recv(4), 'big')
        if version not in [2, 3]:
            self.logger.debug(f'Version {version} is not supported.')
            return
        self.request.send(b'\x01' + socket.inet_aton(self.client_address[0]))  # acknowledge connection
        int.from_bytes(self.request.recv(4), 'big')
        command = int.from_bytes(self.request.recv(1), 'big')
        self.logger.debug(f'Client sent a version {version} command.')
        if command == 1:  # Send PDR (Primary Description Record?), otherwise known as the first blob
            self.logger.debug('Reading PDR blob...')
            fh = open('pdr.bin', 'rb')
            resp = fh.read()
            fh.close()
            self.logger.info('Sending primary description record...')
            self.request.send(len(resp).to_bytes(4, 'big') + resp)
        elif command == 2:
            """
            Send CDR (Content Description Record), otherwise known as the second blob.
            The client actually sends us it's own checksum to verify, instead of redownloading it over again on launch.
            """
            self.logger.debug('Reading client CDR blob hash...')
            client_hash = self.request.recv(21)
            self.logger.debug('Reading CDR blob...')
            fh = open('cdr.bin', 'rb')
            cdr = fh.read()
            fh.close()
            self.logger.debug('Getting checksum of CDR blob...')
            sha1 = hashlib.sha1()
            sha1.update(cdr)
            cdr_hash = sha1.digest()
            self.logger.debug('Comparing hash of CDR blob against client\'s version...')
            if cdr_hash == client_hash:
                self.logger.info('Client has valid content description record.')
                self.request.send(b'\x00\x00\x00\x00')
            else:
                self.logger.info('Client has invalid or newer content description record, sending new blob...')
                self.request.send(len(cdr).to_bytes(4, 'big') + cdr)
        elif command == 4:  # Send network key
            """
            First key ends before \xbf on the second line, second key starts at \xbf on the second life, ends before
            \x02\x01\x11 on the last line.
            """
            self.logger.info('Sending network key...')
            self.request.send(
                cryptography.sign_key_with_rsa(cryptography.network_key, cryptography.primary_signing_key)
            )
        elif command == 7:  # ??
            self.logger.info('Sending response for command 7...')
            self.request.send(int(9).to_bytes(4, 'big') + b'\x00\x01\x31\x2d\x00\x00\x00\x01\x2c')
        elif command == 9:  # ??
            self.logger.info('Sending response for command 9...')
            self.request.send(int(11).to_bytes(4, 'big') + b'\x00\x00\x00\x01\x31\x2d\x00\x00\x00\x01\x2c')
        else:
            self.logger.info(f'Unknown command {command}')
            self.request.send(b'\x00\x00')


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