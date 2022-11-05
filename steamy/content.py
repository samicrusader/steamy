import socket
import socketserver
import logging
from . import cryptography


class ContentServerHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_address = client_address
        self.logger = logging.getLogger(f'ContentServer/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')
        ip = socket.inet_aton('10.0.2.174')

        command = int.from_bytes(self.request.recv(4), 'big')
        self.request.send(b'\x01')  # acknowledge connection
        if command == 3:  # Enter package mode
            self.logger.info('Entered into package mode.')
            while True:
                length = int.from_bytes(self.request.recv(4), 'big')
                if not length:
                    return
                command = int.from_bytes(self.request.recv(4), 'big')
                message = None
                if length != 1:
                    message = self.request.recv((length - 1))
                if command == 0:  # gimme data
                    l = int.from_bytes(message[:8], 'big')
                    if l == bytes():
                        return
                    package_name = message[8:(8+l)].decode()
                    file_name = package_name
                    if package_name.endswith('_rsa_signature'):
                        signature_file_name = package_name
                        file_name = package_name.removesuffix('_rsa_signature')
                    self.logger.debug(f'Opening package {file_name}...')
                    fh = open(file_name, 'rb')
                    data = fh.read()
                    fh.close()
                    if not package_name.endswith('_rsa_signature'):
                        self.logger.info(f'Sending {package_name}...')
                    else:
                        self.logger.info(f'Sending signature for {file_name}...')
                        data = cryptography.sign_message_rsa(cryptography.network_key, data)
                    self.request.send((len(data).to_bytes(4, 'big')) * 2 + data)
                elif command == 2:
                    self.request.send('\x00\x00\x00\x02')  # ??
                    return
                elif command == 3:  # Exit package mode
                    self.logger.info('Exiting package mode...')
                    return
        elif command == 0:
            self.logger.warning('Client entered ?? mode.')
            self.request.send(b'\x00')
            return
        else:
            self.logger.info(f'Unknown command {command}')
            resp = b'\x00\x00'
            self.request.send(len(resp).to_bytes(4, 'big') + resp)
        return


class ContentServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = False
    logger = logging.getLogger('ContentServer')
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
    server = ContentServer(address, ContentServerHandler)
    server.serve_forever()
