import hashlib
import yaml
from .configparser import Settings
from Crypto.Cipher import AES
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Util.number import long_to_bytes

settings = Settings.parse_obj(yaml.safe_load(open('config.yaml')))

primary_key = RSA.construct((
    settings.universe.primary_key.n,
    17,
    settings.universe.primary_key.d
))

primary_signing_key = RSA.construct((
    settings.universe.primary_key.n,
    settings.universe.primary_key.d,
    17
))

network_key = RSA.construct((
    settings.universe.network_key.n,
    17,
    settings.universe.network_key.d
))

network_signing_key = RSA.construct((
    settings.universe.network_key.n,
    settings.universe.network_key.d,
    17
))


def check_message(data: bytes, key: bytes):
    key = key + (b'\x00' * 48)
    if SHA.new(xor(key, b'\\' * 64) + SHA.new(xor(key, b'6' * 64) + data[:-20]).digest()).digest() != data[-20:]:
        return False
    return True


def convert_key_to_data(key: RSA.RsaKey):
    data = b'\x30\x81\x9d\x30\x0d\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01\x05\x00\x03\x81\x8b\x00\x30\x81\x87\x02' \
           b'\x81\x81\x00'
    data += long_to_bytes(key.n)
    data += b'\x02\x01'
    data += long_to_bytes(key.e)
    return data


def decrypt_aes(data: bytes, key: bytes, iv: bytes):
    decrypted = bytes()
    aes = AES.new(key, AES.MODE_CBC, iv)
    for i in range(0, len(data), 16):
        decrypted += aes.decrypt(data[i:(i + 16)])
    return decrypted


def decrypt_rsa(message: bytes, key: RSA.RsaKey):
    message = int.from_bytes(message, 'big')
    #message = pow(message, key.d, key.n)
    message = key._decrypt(message)
    return message.to_bytes(key.size_in_bytes(), 'big').strip(b'\x00')


def encrypt_rsa(message: bytes, key: RSA.RsaKey):
    message = int.from_bytes(message, 'big')
    message = key._encrypt(message)
    return message.to_bytes(key.public_key().size_in_bytes(), 'big')


def get_aes_key(data: bytes, key: RSA.RsaKey):
    data = decrypt_rsa(data, key)
    if len(data) != 127:
        raise ValueError('Encrypted string not 127 bytes')
    checksum_key = xor(SHA.new(data[20:127] + b'\x00\x00\x00\x00').digest(), data[0:20])
    sha_checksum = bytes()
    for i in range(6):
        sha_checksum += SHA.new(checksum_key + i.to_bytes(4, 'big')).digest()
    aes_key = xor(sha_checksum[0:107], data[20:127])
    if aes_key[0:20] != SHA.new('').digest():
        raise ValueError('Control checksum does not match AES key checksum')
    return aes_key[-16:]


def sign_key_with_rsa(key_to_sign: RSA.RsaKey, key: RSA.RsaKey):
    data = convert_key_to_data(key_to_sign)
    signature = sign_message_rsa(key, data)
    return len(data).to_bytes(2, 'big') + data + len(signature).to_bytes(2, 'big') + signature


def sign_message_rsa(key: RSA.RsaKey, message: bytes):
    sha1 = hashlib.sha1()
    sha1.update(message)
    message_hash = sha1.digest()
    digest = b'\x00\x01' + (b'\xff' * int((key.public_key().size_in_bits()) / 8 - 38)) + \
             b'\x000!0\t\x06\x05+\x0e\x03\x02\x1a\x05\x00\x04\x14' + message_hash
    signature = encrypt_rsa(digest, key)
    if len(signature) != 256:
        signature = signature.rjust(int((key.public_key().size_in_bits()) / 8), b'\x00')
    return signature


def xor(first: bytes, second: bytes):
    return bytes([_a ^ _b for _a, _b in zip(first, second)])
