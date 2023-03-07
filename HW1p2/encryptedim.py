import argparse
import socket
import os
import sys
import select
import signal
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256

# Padding and Unpadding Scheme of PKCS#7
# Padding Scheme


def pad(msg, block_size):
    pad_len = block_size - len(msg) % block_size
    padding = bytes([pad_len] * pad_len)
    return msg + padding

# Unpadding Scheme


def unpad(msg):
    padding_len = msg[-1]

    # Check the last byte of data to determine the padding length
    if padding_len > len(msg):
        raise ValueError("Invalid Padding")

    # Check if the padding bytes are equal to the padding length
    for i in range(1, padding_len + 1):
        if msg[-i] != padding_len:
            raise ValueError("Invalid Padding")

    return msg[:-padding_len]

# Setting up Server


class SetupServer:
    def __init__(self, confkey, authkey):
        # Set up host and local port
        self.host = 'localhost'
        self.port = 9999

        self.confkey = confkey.encode('utf-8')
        self.authkey = authkey.encode('utf-8')

        # Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

        # Bind thee socket to the port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

        self.iv = None

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

                    # Generate random IV
                    self.iv = os.urandom(16)

                    # Send IV to client
                    conn.sendall(self.iv)

                # If s is standard input
                elif s is sys.stdin:
                    msg = s.readline()
                    if msg == "":
                        break

                    # If there is connection of client send error
                    if conn in self.Rd:
                        # Encrypt and then MAC Scheme
                        # Generate Key
                        cipher = AES.new(confkey, AES.MODE_CBC, self.iv)
                        # Generate message lenght and encrypted it
                        msg_len = str(len(msg))
                        msg_len_enc = cipher.encrypt(
                            pad(msg_len.encode(), AES.block_size))

                        # Encrypt the original message
                        msg_enc = cipher.encrypt(
                            pad(msg.encode(), AES.block_size))

                        # Compute HMAC
                        hmac1 = HMAC(authkey, self.iv + msg_len_enc,
                                     SHA256).digest()
                        hmac2 = HMAC(authkey, msg_enc, SHA256).digest()

                        # Generate final messages
                        final_msg = iv + msg_len_enc + hmac1 + msg_enc + hmac2
                        # Send the message
                        conn.sendall(final_msg)

                    # If there is no connection of clients send error
                    else:
                        print("No client connection")
                        break

                else:
                    # Retrieve encrypted message from the client
                    data = s.recv(1024)
                    if data:

                        # Grab the data and intialize it
                        iv = data[:16]
                        msg_len = data[16:32]
                        hmac1 = data[32:64]
                        msg = data[64:-32]
                        hmac2 = data[-32:]
                        self.iv = iv

                        # Verify HMAC1 value
                        hmac1_verifier = HMAC.new(
                            self.authkey, self.iv + msg_len, digestmod=SHA256).digest()

                        if hmac1_verifier != hmac1:
                            print("Error: HMAC verification failed")
                            sys.exit(0)

                        # Verify HMAC2 value
                        hmac2_verifier = HMAC.new(
                            self.authkey, msg, digestmod=SHA256).digest()

                        if hmac2_verifier != hmac2:
                            print("Error: HMAC verification failed")
                            sys.exit(0)

                        # Decrypt Message Length
                        cipher = AES.new(self.confkey, AES.MODE_CBC, self.iv)
                        decrypted_msglen = unpad(
                            cipher.decrypt(msg_len), AES.block_size)
                        decrypted_msg = unpad(
                            cipher.decrypt(msg, AES.block_size))

                        # Check if message length is correct
                        if decrypted_msglen != len(decrypted_msg):
                            print("Message length does not match")

                        if decrypted_msg != str(self.iv):
                            sys.stdout.write(decrypted_msg)
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

# Setting up Client


class SetupClient:
    def __init__(self, host, confkey, authkey):
        # Set up host and local port
        self.host = host
        self.port = 9999

        # Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

        self.confkey = confkey.encode('utf-8')
        self.authkey = authkey.encode('utf-8')

        self.iv = None

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
                    data = s.recv(1024)
                    if data:
                        # Grab the data nad initialize
                        iv = data[:16]
                        msg_len = data[16:32]
                        hmac1 = data[32:64]
                        msg = data[64:-32]
                        hmac2 = data[-32:]
                        self.iv = iv

                        # Verify HMAC1 value
                        hmac1_verifier = HMAC.new(
                            self.authkey, self.iv + msg_len, digestmod=SHA256).digest()

                        if hmac1_verifier != hmac1:
                            print("Error: HMAC verification failed")
                            sys.exit(0)

                        # Verify HMAC2 value
                        hmac2_verifier = HMAC.new(
                            self.authkey, msg, digestmod=SHA256).digest()

                        if hmac2_verifier != hmac2:
                            print("Error: HMAC verification failed")
                            sys.exit(0)

                        # Decrypt Message Length
                        cipher = AES.new(self.confkey, AES.MODE_CBC, self.iv)
                        decrypted_msglen = unpad(
                            cipher.decrypt(msg_len), AES.block_size)
                        decrypted_msg = unpad(
                            cipher.decrypt(msg, AES.block_size))

                        # Check if message length is correct
                        if decrypted_msglen != len(decrypted_msg):
                            print("Message length does not match")

                        if decrypted_msg != str(self.iv):
                            sys.stdout.write(decrypted_msg)
                            sys.stdout.flush()

                    else:
                        sys.exit(0)
                else:
                    msg = s.readline()
                    if msg == "":
                        break

                    # Encrypt and then MAC Scheme
                    # Generate Key
                    cipher = AES.new(confkey, AES.MODE_CBC, self.iv)
                    # Generate message lenght and encrypted it
                    msg_len = str(len(msg))
                    msg_len_enc = cipher.encrypt(
                        pad(msg_len.encode(), AES.block_size))

                    # Encrypt the original message
                    msg_enc = cipher.encrypt(
                        pad(msg.encode(), AES.block_size))

                    # Compute HMAC
                    hmac1 = HMAC(authkey, self.iv + msg_len_enc,
                                 SHA256).digest()
                    hmac2 = HMAC(authkey, msg_enc, SHA256).digest()

                    # Generate final messages
                    final_msg = iv + msg_len_enc + hmac1 + msg_enc + hmac2

                    # Send the message
                    self.server.sendall(final_msg)


        # Main Function
if __name__ == '__main__':

    # Argument Handler
    parser = argparse.ArgumentParser()
    parser.add_argument("--s", dest='server', default=False,
                        action="store_true", help="server mode", required=False)
    parser.add_argument("--c", dest='destination', type=str,
                        help="client mode", required=False)

    parser.add_argument('--confkey', dest='confkey', type=str,
                        required=False, help='confidentiality key')
    parser.add_argument('--authkey', dest='authkey', type=str,
                        required=False, help='authentication key')

    args = parser.parse_args()

    if args.server:
        SetupServer(args.confkey, args.authkey)
    elif args.destination:
        SetupClient(args.destination, args.confkey, args.authkey)
    else:
        sys.stdout.write("Please add argument --s or --c 'Destination'\n")
        sys.exit(0)
