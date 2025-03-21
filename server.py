from socket import *
from time import ctime

HOST = 'localhost' # or 127.0.0.1
PORT = 5003
BUFSIZE = 1024

ADDRESS = (HOST, PORT)

# 1. Socket
s = socket(AF_INET, SOCK_STREAM)
# 2. Bind
s.bind(ADDRESS)
# 3. Listen
s.listen(5)

while True:
    print('Waiting for connection...')
    # 4. Accept
    (client, address) = s.accept()
    print(f'... Connection from : {address}')
    client.send(f'Hello, {client} Im server'.encode())

    while True:
        message = client.recv(BUFSIZE)
        message = message.decode()
        if not message:
            print('Connection closed')
            client.close()
            break
        else:
            print(message)
            new_message = input('> ').encode()
            client.send(new_message)