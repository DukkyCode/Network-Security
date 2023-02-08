import socket
import sys
import argparse
import select
import signal


class SetupServer:
    def __init__(self):
        # Set up host and local port
        self.host = 'localhost'
        self.port = 9999

	    #Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

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
                    msg = s.readline()
                    if msg == "":
                        break
                    
                    #If there is no connection of client send error
                    if conn in self.Rd:
                        conn.sendall(msg.encode('utf-8'))
                    else:
                        print("No client connection")
                        break

                else:
                    data = s.recv(1024)
                    if data:
                        data = data.decode('utf-8')
                        sys.stdout.write(data)
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

    def handler(self,sig,frame):
        sys.exit(0)
        self.server.close()

class SetupClient:
    def __init__(self, host):
        # Set up host and local port
        self.host = host
        self.port = 9999

	    #Terminate Signal Handler
        signal.signal(signal.SIGINT, self.handler)

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
                    data = s.recv(1024).decode('utf-8')
                    if data:
                        sys.stdout.write(data)
                        sys.stdout.flush()
                    else:
                        sys.exit(0)
                else:
                    msg = s.readline()
                    if msg == "":
                        break
                    self.server.sendall(msg.encode('utf-8'))
    
    def handler(self,sig,frame):
        self.server.close()
        sys.exit(0)


# Main Function
if __name__ == '__main__':
    # Argument Handler
    parser = argparse.ArgumentParser()
    parser.add_argument("--s", dest='server', default=False,
                        action="store_true", help="server mode", required=False)
    parser.add_argument("--c", dest='destination', type=str,
                        help="client mode", required=False)
    args = parser.parse_args()

    if args.server:
        SetupServer()
    elif args.destination:
        SetupClient(args.destination)
    else:
        sys.stdout.write("Please add argument --s or --c 'Destination'\n")
        sys.exit(0)
