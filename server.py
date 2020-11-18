import socket

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind(('', 32489))
serv.listen(5)

while True:
    conn, addr = serv.accept()
    string = ''
    while True:
        data = str(conn.recv(4096))
        if not data: break
        string += data
        print(string)
    conn.close()
    print('disconnected')
