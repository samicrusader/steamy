from io import BytesIO
from typing import Union


class DescriptionRecord:
    def __init__(self, blob: Union[bytes, str]):
        if type(blob) == str:
            fh = open(blob, 'rb')
            self.blob = fh.read()
            fh.close()
        else:
            self.blob = blob
        self.data = dict()
        self.read()

    def read(self):
        if self.blob[0:2] == b'\x01\x50':  # Primary Description Record (firstblob)
            total_size = int.from_bytes(self.blob[2:6], 'little')
            padding = int.from_bytes(self.blob[6:10], 'little')  # ??
            if total_size + padding != len(self.blob):
                raise ValueError('Description record length does not match length in header')

            blob = BytesIO(self.blob[10:total_size+padding])
            while blob.tell() != ((total_size + padding) - 10):
                name_size = int.from_bytes(blob.read(2), 'little')
                data_size = int.from_bytes(blob.read(4), 'little')
                name = blob.read(name_size)
                data = blob.read(data_size)
                self.data.update({name: data})
        else:
            raise NotImplemented('')


def read_pdr_versions(pdr: bytes):
    pass