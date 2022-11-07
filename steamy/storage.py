from typing import Union
from zlib import compress, decompress


class Package:
    def __init__(self, data: Union[bytes, str]):
        self.compression = 0
        self.files = dict()
        self.files_total = 0
        self.pkg = None
        self.version = 0
        if type(data) == str:
            fh = open(data, 'rb')
            self.pkg = fh.read()
            fh.close()
        elif type(data) == bytes:
            self.pkg = data
        else:
            raise ValueError('Invalid package data (should be file path or bytes)')
        self.parse_footer()
        self.parse_files()

    def parse_footer(self):
        footer = self.pkg[-9:]
        self.version = int.from_bytes(footer[:1], 'little')
        self.compression = int.from_bytes(footer[1:5], 'little')
        self.files_total = int.from_bytes(footer[5:], 'little')

    def parse_files(self):
        if self.files_total == 0:
            raise IOError('No files are in this package')
        i = len(self.pkg) - 25
        for _ in range(self.files_total):
            header = self.pkg[i:i + 16]
            unpacked_size = int.from_bytes(header[:4], 'little')
            packed_size = int.from_bytes(header[4:8], 'little')
            start = int.from_bytes(header[8:12], 'little')
            file_name_len = int.from_bytes(header[12:16], 'little')
            file_name = self.pkg[i - file_name_len:i - 1].decode()
            i = i - (file_name_len + 16)
            self.files.update({file_name: {
                'unpacked_size': unpacked_size,
                'packed_size': packed_size,
                'start': start,
            }})

    def extract_chunks(self, file_name: str):
        if file_name not in self.files.keys():
            raise IOError('File is not in package')
        file = list()
        file_description = self.files[file_name]
        size = file_description['packed_size']
        start = file_description['start']
        while size > 0:
            compressed_len = int.from_bytes(self.pkg[start:start + 4], 'little')
            compressed_start = start + 4
            compressed_end = compressed_start + compressed_len
            file.append(self.pkg[compressed_start:compressed_end])
            start = compressed_end
            size -= compressed_len
        return file

    def unpack_chunks(self, file_name: str):
        if file_name not in self.files.keys():
            raise IOError('File is not in package')
        if 'chunks' not in self.files[file_name].keys():
            raise IOError('File is not unpacked from archive')
        file = bytes()
        for chunk in self.files[file_name]['chunks']:
            file += decompress(chunk)
        return file

    def extract_file(self, file_name: str):
        self.files[file_name]['chunks'] = self.extract_chunks(file_name)
        self.files[file_name]['data'] = self.unpack_chunks(file_name)
        return self.files[file_name]['data']

    def unpack(self):
        for file in self.files.keys():
            self.extract_file(file)

    def pack_chunks(self, file_name: str, new_file: bytes):
        file = list()
        for i in range(0, len(new_file), 32768):
            file.append(compress(new_file[i:(i + 32768)], self.compression))
        self.files[file_name]['chunks'] = file

    def pack_file(self, file_name: str, new_file: bytes):
        if file_name not in self.files.keys():
            self.files.update({file_name: {}})
        self.pack_chunks(file_name, new_file)
        self.files[file_name]['data'] = new_file
        self.files[file_name]['unpacked_size'] = len(new_file)
        self.files[file_name]['packed_size'] = -1
        self.files[file_name]['start'] = -1

    def pack(self):
        self.files_total = len(self.files.keys())
        data = list()
        data_length = 0
        index = list()
        for file_name in self.files.keys():
            packed = 0
            offset = data_length
            for chunk in self.files[file_name]['chunks']:
                chunk = len(chunk).to_bytes(4, 'little') + chunk
                data.append(chunk)
                data_length += len(chunk)
                packed += len(chunk) - 4
            self.files[file_name]['packed_size'] = packed
            self.files[file_name]['start'] = offset
            header = file_name.encode() + b'\x00' + \
                self.files[file_name]['unpacked_size'].to_bytes(4, 'little') + \
                self.files[file_name]['packed_size'].to_bytes(4, 'little') + \
                self.files[file_name]['start'].to_bytes(4, 'little') + \
                (len(file_name) + 1).to_bytes(4, 'little')
            index.insert(0, header)
        self.pkg = b''.join(data) + b''.join(index) + self.version.to_bytes(1, 'little') + \
            self.compression.to_bytes(4, 'little') + self.files_total.to_bytes(4, 'little')
        self.save_pkg('loldongs.pkg')

    def save_pkg(self, file_name: str):
        fh = open(file_name, 'wb')
        fh.write(self.pkg)
        fh.close()


class Storage:
    pass
