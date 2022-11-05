import logging
import threading
from steamy.directory import run as DirectoryServer
from steamy.config import run as ConfigServer
from steamy.content_list import run as ContentListServer
from steamy.content import run as ContentServer

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

logging.basicConfig(level=logging.DEBUG)
t1 = threading.Thread(target=DirectoryServer, args=('0.0.0.0', 27038))
t2 = threading.Thread(target=ConfigServer, args=('0.0.0.0', 27035))
t3 = threading.Thread(target=ContentListServer, args=('0.0.0.0', 27037))
t4 = threading.Thread(target=ContentServer, args=('0.0.0.0', 27032))
t1.start()
t2.start()
t3.start()
t4.start()