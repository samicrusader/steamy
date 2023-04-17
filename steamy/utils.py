import yaml
from .configparser import Settings
from datetime import datetime
from io import BytesIO

settings = Settings.parse_obj(yaml.safe_load(open('config.yaml')))

ip = '10.0.2.174'
search_list = {
    '30820120300d06092a864886f70d01010105000382010d00308201080282010100d1543176ee6741270dc1a32f4b04c3a304d499ad0570777d'
    'ba31483d01eb5e639a05eb284f93cf9260b1ef9e159403ae5f7d3997e789646cfc70f26815169a9b4ba4dc5700ea4480f78466eae6d2bdf5e4'
    '181da076ca2e95b32b79c016eb91b5f158e8448d2dd5a42f883976a935dcccbbc611dc2bdf0ea3b88ca72fba919501fb8c6187b4ecddbbb662'
    '3d640e819302a6be35be74460cbad9bff0ab7dff0c5b4b8f4aff8252815989ec5fffb460166c5a75b81dd99d79b05f23d97476eb3a5d44c74d'
    'cd1136e776f5d2bb52e77f530fa2a5ad75f16c1fb5d8218d71b93073bddad930b3b4217989aa58b30566f1887907ca431e02defe51d1948948'
    '6caf033d020111': f'30820120300d06092a864886f70d01010105000382010d00308201080282010100{settings.universe.primary_key.n:x}020111', # Main RSA key
    'gds1.steampowered.com:27030 gds2.steampowered.com:27030': f'{ip}:27030 {ip}:27030',  # ContentList (?)
    '72.165.61.189:27030 72.165.61.190:27030 69.28.151.178:27038 69.28.153.82:27038 87.248.196.194:27038 '
    '68.142.72.250:27038': f'{ip}:27030 {ip}:27030 {ip}:27038 {ip}:27038 {ip}:27038 {ip}:27038 ',
    '207.173.176.215': ip, '72.165.61.188': ip, '72.165.61.187': ip, '72.165.61.186': ip, '72.165.61.185': ip,
    '208.111.133.85': ip, '208.111.133.84': ip, '68.142.91.35': ip, '68.142.91.34': ip, '208.111.171.83': ip,
    '208.111.171.82': ip, '208.111.158.53': ip, '208.111.158.52': ip, '69.28.145.171': ip, '69.28.145.170': ip,
    '207.173.177.11:27030 207.173.177.12:27030 69.28.151.178:27038 69.28.153.82:27038 68.142.88.34:27038 68.142.72.250:'
    '27038 ':
        f'{ip}:27030 {ip}:27030 {ip}:27038 {ip}:27038 {ip}:27038 {ip}:27038 ',
    '207.173.179.14': ip, '207.173.179.198': ip, '207.173.178.196': ip, '207.173.178.214': ip, '68.142.64.166': ip,
    '68.142.64.166': ip, '68.142.64.165': ip, '68.142.64.164': ip, '68.142.64.163': ip, '68.142.64.162': ip,
    '69.28.156.250': ip, '69.28.148.250': ip, '207.173.178.198': ip, '207.173.176.216': ip, '207.173.179.87': ip,
    '207.173.178.127': ip, '207.173.178.178': ip, '68.142.88.24': ip,
    '207.173.177.11:27030 207.173.177.12:27030 69.28.151.178:27038 69.28.153.82:27038 68.142.88.34:27038 68.142.72.250:'
    '27038': f'{ip}:27030 {ip}:27030 {ip}:27038 {ip}:27038 {ip}:27038 {ip}:27038',
}


def replace(binary: bytes, replace_list: dict = search_list):
    f = BytesIO(binary)  # This is a really cheap hack but effective.
    for search, replace in replace_list.items():
        if len(replace) > len(search):
            raise ValueError('Replacement data is bigger than search')
        loc = binary.find(search.encode())
        if loc != -1:
            f.seek(loc)
            f.write(replace.encode()+b'\x00')
    f.seek(0)
    return f.read()


def valve_time(dt: datetime = datetime.now()):
    """
    See https://developer.valvesoftware.com/wiki/Valve_Time for the joke.

    Converts a datetime.datetime object to a valid timestamp that the Steam client likes.

    :param dt: datetime.datetime
    :return: bytes
    """
    epoch = datetime.timestamp(dt)
    timestamp = int((epoch + 62135596800) * 1000000)
    return timestamp.to_bytes(8, 'little')


def deserialize(blob: bytes):
    data = dict()
    if blob[:2] != b'\x01P':
        raise ValueError('Data is not a serialized blob')
    size = int.from_bytes(blob[2:6], 'little')
    padding_size = int.from_bytes(blob[6:10], 'little')
    if padding_size:
        data['__padding__'] = blob[-padding_size:]
    if (size + padding_size) > len(blob):
        raise ValueError(f'Data length ({len(blob)}) does not match length in header ({size + padding_size}).')
    f = BytesIO(blob[10:])
    while f.tell() != ((size + padding_size) - 10):
        name_size = int.from_bytes(f.read(2), 'little')
        data_size = int.from_bytes(f.read(4), 'little')
        name = f.read(name_size)
        blob_data = f.read(data_size)
        if blob_data[:2] == b'\x01P':
            data[name] = deserialize(blob_data)
        else:
            data[name] = blob_data
    print(data)
    return data
