import socket
from contextlib import closing

with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
    sock.settimeout(2)
    if sock.connect_ex(("db", 5432)) == 0:
        exit(0)
    else:
        exit(1)
