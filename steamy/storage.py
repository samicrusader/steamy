from typing import Union
from zlib import compress, decompress

class Package:
    compression = 0
    files = dict()
    files_total = 0
    pkg = None
    version = 0

    def __init__(self, data: Union[bytes, str]):
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
            raise ValueError('No files are in this package')
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

    def extract_file(self, file_name: str):
        if file_name not in self.files.keys():
            raise ValueError('File is not in package')
        file = bytes()
        file_description = self.files[file_name]
        size = file_description['packed_size']
        start = file_description['start']
        while size > 0:
            compressed_len = int.from_bytes(self.pkg[start:start + 4], 'little')
            compressed_start = start + 4
            compressed_end = compressed_start + compressed_len
            file += decompress(self.pkg[compressed_start:compressed_end])
            start = compressed_end
            size -= compressed_len
        if len(file) != file_description['unpacked_size']:
            raise IOError('File length does not match size in package')
        return file


class Storage:
    pass