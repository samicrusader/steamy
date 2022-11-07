import socket
import socketserver
import logging


class AuthServerHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_address = client_address
        self.logger = logging.getLogger(f'AuthServer/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')
        request_line = self.request.recv(13)  # 4 bytes of NUL + the IP address + 4 more bytes of NUL
        self.logger.debug(f'Client IP address in request is {socket.inet_ntoa(request_line[5:9][::-1])}')
        self.request.send(b'\x00' + socket.inet_aton(self.client_address[0]))  # acknowledge connection
        length = int.from_bytes(self.request.recv(4), 'big')
        message = self.request.recv(length)
        command = int.from_bytes(message[:1], 'big')
        if command == 2:  # Normal login
            username = message[3:(3 + int.from_bytes(message[1:3], 'big'))]
            print(username)
            # REMOVE STARTING HERE
            ul = int.from_bytes(message[1:3], 'big')
            ul = ul + 5
            username2 = message[ul:(ul+int.from_bytes(message[(ul-5):ul], 'big'))]
            if username != username2:
                self.logger.warning(f'1st username in request {username} does not match {username2}')
            # REMOVE ENDING HERE
        else:
            self.logger.info(f'Unknown command {command}')
        resp = b'\x00\x00'
        self.request.send(len(resp).to_bytes(4, 'big') + resp)
        return


class AuthServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = False
    logger = logging.getLogger('AuthServer')
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
    server = AuthServer(address, AuthServerHandler)
    server.serve_forever()
