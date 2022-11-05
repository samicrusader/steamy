import socket
import socketserver
import logging


class DirectoryServerHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger(f'DirectoryServer/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')
        ip = socket.inet_aton('10.0.2.174')

        # Echo the back to the client
        version = int.from_bytes(self.request.recv(4), 'little')
        self.request.send(b'\x01')  # acknowledge connection
        length = int.from_bytes(self.request.recv(4), 'little')
        if len(length) is not 4:
            self.logger.debug('Invalid header from client.')
            self.request.send(b'\x00\x00')
            self.finish()
            return
        message = self.request.read(length)
        self.logger.debug(f'Client sent a version {version} command.')
        command = message[0]
        port = None
        if command is b'\x00' or command is b'\x0b':  # Send auth server
            if version is 1:
                self.logger.debug('Sending auth server...')
            elif version is 2:
                self.logger.debug(f'Sending auth server for user {command}...')
            port = int.to_bytes(27039, 2, 'little')
        elif command is b'\x03':  # Send config server
            self.logger.debug('Sending config server...')
            port = int.to_bytes(27035, 2, 'little')
        elif command is b'\x06':  # Send content list server
            self.logger.debug('Sending content list server...')
            port = int.to_bytes(27037, 2, 'little')
        elif command is b'\x0f' or command is b'\x18' or command is b'\x1e':  # Send (Gold)Source & RKDF master servers
            """
            command \x1e is RDKF
            Could it be Rag Doll Kung Fu? It did release from 2005, and is the first non-Valve Steam game.
            https://store.steampowered.com/app/1002/Rag_Doll_Kung_Fu/
            """
            self.logger.debug('Sending game master servers...')
            port = int.to_bytes(27010, 2, 'little')
        elif command is b'\x12':  # Send account retrieval server
            self.logger.debug('Sending account retrieval server...')
            port = int.to_bytes(6969, 2, 'little')  # A shot in the dark to get MAYBE an implementation going
        elif command is b'\x14':  # Send game statistic (CSER) server
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
        elif command is b'\x1c' and version is 2:  # Send content server
            self.logger.debug('Sending content server...')
            if message is not b'\x1c\x60\x0f\x2d\x40':  # The fuck?
                self.logger.info(f'Content server message isnt the usual: {message}')
            port = int.to_bytes(27037, 2, 'little')  # Just send it anyways...
        if port:
            self.request.send(b'\x00\x01' + ip + port)
        else:
            self.request.send(b'\x00\x00')
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
