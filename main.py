import logging
import threading
import shutil
import os
import yaml
from steamy.auth import run as AuthServer
from steamy.directory import run as DirectoryServer
from steamy.config import run as ConfigServer
from steamy.configparser import Settings
from steamy.content_list import run as ContentListServer
from steamy.content import run as ContentServer
from steamy.storage import Package
from steamy.utils import replace
from steamy.description_records import DescriptionRecord
from steamy.cser import run as CSER

settings = Settings.parse_obj(yaml.safe_load(open('config.yaml')))

# Get SteamNew.exe
try:
    shutil.rmtree('./client')
except:
    pass
os.mkdir('./client')
pdr = DescriptionRecord('pdr.bin').data
client_version = int.from_bytes(pdr[b"\x01\x00\x00\x00"], "little")
client_version = f'Steam_{client_version}.pkg'
ui_version = int.from_bytes(pdr[b"\x02\x00\x00\x00"], "little")
ui_version =  f'SteamUI_{ui_version}.pkg'
if not os.path.exists(client_version):
    raise IOError(f'Client package {client_version} missing')
if not os.path.exists(ui_version):
    raise IOError(f'Client package {ui_version} missing')
p = Package(client_version)
exe = p.extract_file('SteamNew.exe')
exe = replace(exe)
fh = open('./client/Steam.exe', 'wb')
fh.write(exe)
fh.close()
del exe

logging.basicConfig(level=logging.DEBUG)
t1 = threading.Thread(target=DirectoryServer, args=('0.0.0.0', 27038))
t2 = threading.Thread(target=ConfigServer, args=('0.0.0.0', 27035))
t3 = threading.Thread(target=ContentListServer, args=('0.0.0.0', 27037))
t4 = threading.Thread(target=ContentServer, args=('0.0.0.0', 27032))
t5 = threading.Thread(target=AuthServer, args=('0.0.0.0', 27039))
t6 = threading.Thread(target=CSER, args=('0.0.0.0', 27013))
t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()
