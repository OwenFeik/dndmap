import socket
import sys
import time

message = sys.argv[1].encode()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False)
sock.connect_ex(('127.0.0.1', 32489))

while True:
    sock.send(message)
    print(str(sock.recv(4096)))
    time.sleep(2)

sock.close()
