import selectors
import socket
import types

sel = selectors.DefaultSelector()

def accept_connection(sock):
    conn, addr = sock.accept()
    print(f'accepted connection from {addr}')
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print(f'closing connection to {data.addr}')
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f'sending {data.outb} to {data.addr}')
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

def main_loop():
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_connection(key.fileobj)
            else:
                service_connection(key, mask)

if __name__ == '__main__':
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.bind(('', 32489))
    serv.listen()
    serv.setblocking(False)
    sel.register(serv, selectors.EVENT_READ, data=None)

    main_loop()
