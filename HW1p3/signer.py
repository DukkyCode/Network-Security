from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

import socket
import sys
import argparse
import select
import signal
import binascii

#Global Variables
global privkey_path
global pubkey_path

privkey_path = './privatekey.pem'
pubkey_path = './pubkey.pem'

#Padding Function 
def mypad(somenum):
    return '0' * (4-len(str(somenum))) + str(somenum)

#Generate RSA Key Pair
class GenKey():
    def __init__(self):
        self.keypair = RSA.generate(4096)
        
        #Write Public Key into file
        with open(pubkey_path, 'w') as file:
            file.write(self.keypair.publickey().export_key().encode())

        #Write Private Key into file
        with open(privkey_path, 'w') as file:
            file.write(self.keypair.export_key().encode())


class SetupClient:
    def __init__(self, host, message):
        # Set up host, local port and message
        self.host = host
        self.port = 9998
        self.msg = message

        # Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

        # Bind thee socket to the port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.connect((self.host, self.port))

        #Padded Message Length
        self.pad_msg_len = mypad(len(self.msg))
        
        #Create a Hash Object of the Message
        self.digest = SHA256.new(self.msg.encode('utf-8'))

        #Write Private Key into file
        with open(privkey_path, 'r') as file:
            self.privkey = file.read()

        #Get the Signature
        self.privkey = RSA.import_key(self.privkey)        
        self.pkcs = pkcs1_15.new(self.privkey)
        self.signature = self.pkcs.sign(self.digest)

        self.signature_hex = binascii.hexlify(self.signature)
        self.len_signature_hex = mypad(len(self.signature_hex))

        #Sending all the Message and exit
        self.server.sendall(self.pad_msg_len.encode('utf-8'))
        self.server.sendall(self.msg.encode('utf-8'))
        self.server.sendall(self.len_signature_hex.encode('utf-8'))
        self.server.sendall(self.signature_hex)

        sys.exit(0)
        
        # # Read and Write File Descriptor
        # self.Rd = [self.server, sys.stdin]
        # self.Wd = []

        # while self.Rd:
        #     readable, writable, exceptional = select.select(
        #         self.Rd, self.Wd, self.Rd)

        #     for s in readable:
        #         # If the connection is established
        #         if s is self.server:
        #             data = s.recv(1024).decode('utf-8')
        #             if data:
        #                 sys.stdout.write(data)
        #                 sys.stdout.flush()
        #             else:
        #                 sys.exit(0)
        #         else:
        #             msg = s.readline()
        #             if msg == "":
        #                 break
        #             self.server.sendall(msg.encode('utf-8'))

    def handler(self, sig, frame):
        self.server.close()
        sys.exit(0)

# Main Function
if __name__ == '__main__':
    # Argument Handler
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--genkey", dest='genkey', default=False, action="store_true", help="Generate RSA Key Pair", required=False)
    parser.add_argument("--c", dest='destination', type=str, help="Client Mode", required=False)
    parser.add_argument("--m", dest='message', type=str, help="Message to sent", required=False)

    args = parser.parse_args()

    if args.genkey:
        GenKey()
    elif args.destination:
        SetupClient(args.destination, args.message)
    else:
        sys.stdout.write("Please add argument --genkey or --c 'Destination'\n")
        sys.exit(0)