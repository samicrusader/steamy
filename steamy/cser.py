import socketserver
import logging
from io import BytesIO


class CSERHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.client_address = client_address
        self.logger = logging.getLogger(f'CSER/{self.client_address[0]}:{self.client_address[1]}')
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')
        data = BytesIO(self.request[0])
        if data.read(1) == b'e':  # Client statistics
            exe_length = int.from_bytes(data.read(1), 'little')
            data.read(1)  # '\x01'
            exe_name = data.read(exe_length).strip(b'\x00').decode()
            stats = dict()
            for i in ['SuccessCount', 'UnknownFailureCount', 'ShutdownFailureCount', 'UptimeCleanCounter',
                      'UptimeCleanTotal', 'UptimeFailureCounter', 'UptimeFailureTotal']:
                stats[i] = int.from_bytes(data.read(4), 'little')
            self.logger.info(f'Client statistics data from {exe_name} on {self.client_address[0]}: {stats}')
        else:
            self.logger.info(f'Client sent unknown statistics data')


class CSER(socketserver.ThreadingUDPServer):
    allow_reuse_address = True
    daemon_threads = False
    logger = logging.getLogger('CSER')
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
    server = CSER(address, CSERHandler)
    server.serve_forever()