import socket
import socketserver
import logging


class ContentListHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_address = client_address
        self.logger = logging.getLogger(f'ContentListServer/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')
        ip = socket.inet_aton('10.0.2.174')

        version = int.from_bytes(self.request.recv(4), 'big')
        if version not in [2]:
            self.logger.debug(f'Version {version} is not supported.')
            return
        self.request.send(b'\x01')  # acknowledge connection
        length = int.from_bytes(self.request.recv(4), 'big')
        command = int.from_bytes(self.request.recv(1), 'big')
        message = None
        if length != 1:
            message = self.request.recv((length - 1))
            print('message:', message)
        self.logger.debug(f'Client sent a version {version} command.')
        if command == 0:  # Send file servers that hold a specific package
            print(message)
            resp = b'\x00\x01\x00\x00\x00\x00' + ip + int.to_bytes(27032, 2, 'little') + ip +\
                   int.to_bytes(27032, 2, 'little')
            self.request.send(len(resp).to_bytes(4, 'big') + resp)
        else:
            self.logger.info(f'Unknown command {command}')
            resp = b'\x00\x00'
        self.request.send(len(resp).to_bytes(4, 'big') + resp)
        return


class ContentListServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = False
    logger = logging.getLogger('ContentListServer')
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
    server = ContentListServer(address, ContentListHandler)
    server.serve_forever()
