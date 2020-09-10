import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('58.96.73.113', 32489))
sock.send(b'compelling argument')
sock.recv(4096)
sock.close()
