import argparse
import socket
import os
import sys
import select
import signal
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256


#Global Variables
global iv
global encryptor
global decryptor

# Padding and Unpadding Scheme of PKCS#7
# Padding Scheme
def pad(msg, block_size):
    pad_size = block_size - len(msg) % block_size
    padding = chr(pad_size) * pad_size
    return msg + padding

# Unpadding Scheme
def unpad(msg):
    pad_size = ord(msg[-1])
    return msg[:-pad_size]
    
class SetupServer:
    def __init__(self, confkey, authkey):
        # Set up host and local port
        self.host = 'localhost'
        self.port = 9999

        # Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

        #Initialize configuration key and authentication key
        self.confkey = confkey.encode('utf-8')
        self.authkey = authkey.encode('utf-8')

        # Bind thee socket to the port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

        # Listen for incoming
        self.server.listen(1)
        # Read and Write File Descriptor
        self.Rd = [self.server, sys.stdin]
        self.Wd = []

        while self.Rd:
            readable, writable, exceptional = select.select(
                self.Rd, self.Wd, self.Rd)

            for s in readable:
                if s is self.server:
                    # Accepting connection from client
                    conn, addr = s.accept()
                    self.Rd.append(conn)

                # If s is standard input
                elif s is sys.stdin:
                    iv = os.urandom(16)
                    msg = s.readline()
                    if msg == "":
                        break

                    # If there is no connection of client send error
                    if conn in self.Rd:
                        encryptor = AES.new(self.confkey, AES.MODE_CBC, iv)
                        
                        #Encrypt Message Length
                        msg_len = str(len(msg))
                        pad_msglen = pad(msg_len, AES.block_size)
                        msg_len = encryptor.encrypt(pad_msglen.encode('utf-8'))

                        #Encrypt Message
                        pad_msg = pad(msg, AES.block_size)
                        msg = encryptor.encrypt(pad_msg.encode('utf-8'))

                        #Generate MAC
                        hmac1 = HMAC.new(self.authkey, iv + msg_len, digestmod= SHA256).digest()
                        hmac2 = HMAC.new(self.authkey, msg, digestmod= SHA256).digest()

                        #Sending Message
                        message = iv + msg_len + hmac1 + msg + hmac2

                        conn.sendall(message)
                    else:
                        print("No client connection")
                        break

                else:
                    data = s.recv(2048)
                    if data:
                        iv = data[:16]
                        msg_len = data[16:32]
                        hmac1 = data[32:64]
                        msg = data[64:-32]
                        hmac2 = data[-32:]

                        decryptor = AES.new(self.confkey, AES.MODE_CBC, iv)

                        hmac1_verify = HMAC.new(self.authkey, iv + msg_len, digestmod=SHA256).digest()
                        hmac2_verify = HMAC.new(self.authkey, msg, digestmod=SHA256).digest()

                        if(hmac1_verify != hmac1) or (hmac2_verify != hmac2):
                            print("ERROR: HMAC verification failed")
                            sys.exit(0)
                        
                        temp = decryptor.decrypt(msg_len).decode('utf-8')
                        msg_len = int(unpad(temp))

                        temp = decryptor.decrypt(msg).decode('utf-8')
                        msg = unpad(temp)

                        if msg_len != len(msg):
                            print("Length does not match")
                            
                        sys.stdout.write(msg)
                        sys.stdout.flush()

                        # if the connection is not in Write file description, then append it into the list
                        if s not in self.Wd:
                            self.Wd.append(s)
                    # If there is no data, no connection
                    else:
                        if s in self.Wd:
                            self.Wd.remove(s)
                        self.Rd.remove(s)
                        s.close()

    def handler(self, sig, frame):
        sys.exit(0)
        self.server.close()


class SetupClient:
    def __init__(self, host, confkey, authkey):
        # Set up host and local port
        self.host = host
        self.port = 9999

        # Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

        #Initialize configuration key and authentication key
        self.confkey = confkey.encode('utf-8')
        self.authkey = authkey.encode('utf-8')

        # Bind thee socket to the port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.connect((self.host, self.port))

        # Read and Write File Descriptor
        self.Rd = [self.server, sys.stdin]
        self.Wd = []

        while self.Rd:
            readable, writable, exceptional = select.select(
                self.Rd, self.Wd, self.Rd)

            for s in readable:
                # If the connection is established
                if s is self.server:
                    data = s.recv(2048)
                    if data:
                        iv = data[:16]
                        msg_len = data[16:32]
                        hmac1 = data[32:64]
                        msg = data[64:-32]
                        hmac2 = data[-32:]

                        decryptor = AES.new(self.confkey, AES.MODE_CBC, iv)

                        hmac1_verify = HMAC.new(self.authkey, iv + msg_len, digestmod=SHA256).digest()
                        hmac2_verify = HMAC.new(self.authkey, msg, digestmod=SHA256).digest()

                        if hmac1_verify != hmac1:
                            print("ERROR: HMAC verification failed")
                            sys.exit(0)

                        if hmac2_verify != hmac2:
                            print("ERROR: HMAC verification failed")
                            sys.exit(0)

                        temp = decryptor.decrypt(msg_len).decode('utf-8')
                        msg_len = int(unpad(temp))

                        temp = decryptor.decrypt(msg).decode('utf-8')
                        msg = unpad(temp)

                        if msg_len != len(msg):
                            print("Length does not match")
                            
                        sys.stdout.write(msg)
                        sys.stdout.flush()
                    else:
                        sys.exit(0)
                else:
                    iv = os.urandom(16)
                    msg = s.readline()
                    if msg == "":
                        break

                    encryptor = AES.new(self.confkey, AES.MODE_CBC, iv)
                    
                    #Encrypt Message Length
                    msg_len = str(len(msg))
                    pad_msglen = pad(msg_len, AES.block_size)
                    msg_len = encryptor.encrypt(pad_msglen.encode('utf-8'))

                    #Encrypt Message
                    pad_msg = pad(msg, AES.block_size)
                    msg = encryptor.encrypt(pad_msg.encode('utf-8'))

                    #Generate MAC
                    hmac1 = HMAC.new(self.authkey, iv + msg_len, digestmod= SHA256).digest()
                    hmac2 = HMAC.new(self.authkey, msg, digestmod= SHA256).digest()

                    #Sending Message
                    message = iv + msg_len + hmac1 + msg + hmac2

                    self.server.sendall(message)

    def handler(self, sig, frame):
        self.server.close()
        sys.exit(0)

# Main Function
if __name__ == '__main__':

    # Argument Handler
    parser = argparse.ArgumentParser()
    parser.add_argument("--s", dest='server', default=False, action="store_true", help="server mode", required=False)
    parser.add_argument("--c", dest='destination', type=str,help="client mode", required=False)

    parser.add_argument('--confkey', dest='confkey', type=str,required=False, help='confidentiality key')
    parser.add_argument('--authkey', dest='authkey', type=str,required=False, help='authentication key')

    args = parser.parse_args()

    if len(args.confkey.encode()) < 32:
        args.confkey += (32 - len(args.confkey.encode())) * '1'

    if args.server:
        SetupServer(args.confkey, args.authkey)
    elif args.destination:
        SetupClient(args.destination, args.confkey, args.authkey)
    else:
        sys.stdout.write("Please add argument --s or --c 'Destination'\n")
        sys.exit(0)
