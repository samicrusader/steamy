import socketserver
import logging


class DirectoryServerHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('DirectoryServer')
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')

        # Echo the back to the client
        version = int.from_bytes(self.request.recv(4), 'little')
        self.request.send(b'\x01')  # acknowledge connection
        length = int.from_bytes(self.request.recv(4), 'little')
        if len(length) is not 4:
            logging.debug(f'Invalid header from client {self.client_address[0]}')
            self.finish()
        message = self.request.read(length)
        logging.debug(f'Client {self.client_address[0]} sent a version {version} command')

        return


class DirectoryServer(socketserver.TCPServer):
    def __init__(self, server_address, handler_class=DirectoryServerHandler):
        self.logger = logging.getLogger('DirectoryServer')
        self.logger.debug('__init__')
        socketserver.TCPServer.__init__(self, server_address, handler_class)
        return

    def serve_forever(self):
        self.logger.info('Server is listening')
        while True:
            self.handle_request()
        return

    def server_close(self):
        self.logger.info('stopping server...')
        return socketserver.TCPServer.server_close(self)

    def process_request(self, request, client_address):
        self.logger.debug(f'Connection established from {client_address}')
        return socketserver.TCPServer.process_request(self, request, client_address)


def run(ip: str, port: int):
    address = (ip, port)  # let the kernel give us a port
    server = DirectoryServer(address, DirectoryServerHandler)
    server.serve_forever()
