from socket import *

HOST = 'localhost'
PORT = 5000
ADDRESS = (HOST, PORT)

BUFSIZE = 1024

# 1. Socket
s = socket(AF_INET, SOCK_STREAM)
# 2. Connect
s.connect(ADDRESS)
# 3. Receive data
received_message = s.recv(BUFSIZE)
print(received_message.decode(ascii))
s.close()