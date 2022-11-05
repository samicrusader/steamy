import socket
import socketserver
import logging


class DirectoryServerHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_address = client_address
        self.logger = logging.getLogger(f'DirectoryServer/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')
        ip = socket.inet_aton('10.0.2.174')

        # Echo the back to the client
        version = int.from_bytes(self.request.recv(4), 'big')
        if version not in [1, 2]:
            self.logger.debug(f'Version {version} is not supported.')
            return
        self.request.send(b'\x01')  # acknowledge connection
        length = int.from_bytes(self.request.recv(4), 'big')
        command = int.from_bytes(self.request.recv(1), 'big')
        if length != 1:
            message = self.request.recv((length - 1))
            print('message:', message)
        self.logger.debug(f'Client sent a version {version} command.')
        port = None
        if command == 0 or command == 11:  # Send auth server
            if version == 1:
                self.logger.debug('Sending auth server...')
            elif version == 2:
                self.logger.debug(f'Sending auth server for user {command}...')
            port = int.to_bytes(27039, 2, 'little')
        elif command == 3:  # Send config server
            self.logger.debug('Sending config server...')
            port = int.to_bytes(27035, 2, 'little')
        elif command == 6:  # Send content list server
            self.logger.debug('Sending content list server...')
            port = int.to_bytes(27037, 2, 'little')
        elif command == 15 or command == 24 or command == 30:  # Send (Gold)Source & RKDF master servers
            """
            command \x1e is RDKF
            Could it be Rag Doll Kung Fu? It did release from 2005, and is the first non-Valve Steam game.
            https://store.steampowered.com/app/1002/Rag_Doll_Kung_Fu/
            """
            self.logger.debug('Sending game master servers...')
            port = int.to_bytes(27010, 2, 'little')
        elif command == 18:  # Send account retrieval server
            self.logger.debug('Sending account retrieval server...')
            port = int.to_bytes(6969, 2, 'little')  # A shot in the dark to get MAYBE an implementation going
        elif command == 20:  # Send game statistic (CSER) server
            """
            https://github.com/ValveSoftware/source-sdk-2013/blob/master/sp/src/game/shared/gamestats.h
            and
            https://developer.valvesoftware.com/wiki/Command_Line_Options:# Command-Line Parameters
            ...
            -localcser	Sets a custom gamestats CSER other than the Steam-provided public one (default is
            steambeta1:27013)
            ...
            """
            self.logger.debug('Sending CSER server...')
            port = int.to_bytes(27037, 2, 'little')
        elif command == 28 and version == 2:  # Send content server
            self.logger.debug('Sending content server...')
            if message != b'\x1c\x60\x0f\x2d\x40':  # The fuck?
                self.logger.info(f'Content server message isnt the usual: {message}')
            port = int.to_bytes(27037, 2, 'little')  # Just send it anyways...
        else:
            self.logger.debug(f'Unknown command {command}')
        if port:
            resp = b'\x00\x01' + ip + port
        else:
            resp = self.request.send(b'\x00\x00')
        self.request.send(len(resp).to_bytes(4, 'big') + resp)
        return


class DirectoryServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = False
    logger = logging.getLogger('DirectoryServer')
    logger.setLevel(logging.DEBUG)

    def serve_forever(self):
        self.logger.info('Server is listening')
        return socketserver.ThreadingTCPServer.serve_forever(self)

    def server_close(self):
        self.logger.info('stopping server...')
        return socketserver.ThreadingTCPServer.server_close(self)

    def process_request(self, request, client_address):
        self.logger.debug(f'Connection established from {client_address}')
        return socketserver.ThreadingTCPServer.process_request(self, request, client_address)


def run(ip: str, port: int):
    address = (ip, port)  # let the kernel give us a port
    server = DirectoryServer(address, DirectoryServerHandler)
    server.serve_forever()
