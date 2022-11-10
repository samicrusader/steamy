import socket
import socketserver
import logging
from . import cryptography
from .database import engine, User as DBUser
from .utils import deserialize, valve_time
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker

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
        db_session = scoped_session(sessionmaker(bind=engine))
        if command in [1, 14, 29, 32, 33, 34]:
            self.request.send(
                cryptography.sign_key_with_rsa(cryptography.network_key, cryptography.primary_signing_key)
            )
            message = self.request.recv(int.from_bytes(self.request.recv(4), 'big'))
            key = cryptography.get_aes_key(message[2:130], cryptography.network_key)
            message = message[144:]
            length = int.from_bytes(message[:4], 'big')
            if not cryptography.check_message(message, key):
                self.logger.error('AES message check failed')
                self.request.send(b'\x00')
                return
            message = cryptography.decrypt_aes(message[20:-20], key, message[4:20])[:length]
            message = deserialize(message)
        if command == 1:  # Registration
            username = message[b'\x01\x00\x00\x00'].decode().strip('\x00')
            user = DBUser(
                username=username,
                email=message[b'\x0b\x00\x00\x00'].decode().strip('\x00'),
                disabled=False,
                key=message[b'\x05\x00\x00\x00'][username.encode()][b'\x01\x00\x00\x00'],
                salt=message[b'\x05\x00\x00\x00'][username.encode()][b'\x02\x00\x00\x00'],
                password=message[b'\x05\x00\x00\x00'][username.encode()][b'\x04\x00\x00\x00'],
                recovery_question=message[b'\x05\x00\x00\x00'][username.encode()][b'\x03\x00\x00\x00'],
                recovery_answer=message[b'\x05\x00\x00\x00'][username.encode()][b'\x05\x00\x00\x00'],
                unknown_data=message[b'\x02\x00\x00\x00']
            )
            try:
                db_session.add(user)
                db_session.commit()
            except SQLAlchemyError as e:  # TODO: Return specific errors
                self.logger.error(f'Error while registering user {username}: {e}')
                resp = b'\x01'
            else:
                self.logger.info(f'User {username} registered')
                resp = b'\x00'
        elif command == 2:  # Normal login
            user_name = message[3:(3 + int.from_bytes(message[1:3], 'big'))].decode()
            self.logger.info(f'Logging into {user_name}...')
            try:
                user_object = db_session.query(DBUser).filter(DBUser.username == user_name)[0]
            except IndexError:
                pass  # Wrong username
            else:
                self.logger.debug(f'{user_name} is in the database.')
            self.request.send(b'\x00\x00\x00\x00\x00\x00\x00\x00')
            self.request.send(b'\x01' + valve_time() + (b'\x00' * 1222))
            return
        elif command == 29:  # Check username
            username = message[b'\x01\x00\x00\x00'].decode().strip('\x00')
            self.logger.info(f'Client wants to know if username "{username}" is available.')
            try:
                db_session.query(DBUser).filter(DBUser.username == username)[0]
            except IndexError:
                self.logger.debug(f'"{username}" is available')
                resp = b'\x01'
            else:
                self.logger.debug(f'"{username}" is unavailable')
                resp = b'\x00'
        elif command == 34:  # Check email
            email = message[b"\x01\x00\x00\x00"].decode().strip('\x00')
            self.logger.info(f'Client wants to know if username "{email}" is available.')
            try:
                db_session.query(DBUser).filter(DBUser.email == email)[0]
            except IndexError:
                self.logger.debug(f'"{email}" is available')
                resp = b'\x01'
            else:
                self.logger.debug(f'"{email}" is unavailable')
                resp = b'\x00'
        else:
            self.logger.info(f'Unknown command {command}')
            resp = b'\x00'
        self.request.send(resp)
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
