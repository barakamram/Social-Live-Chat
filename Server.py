import pickle
import socket
import threading
from struct import pack
import time

# HOST = "127.0.1.1"
HOST = "192.168.1.206"
# HOST = "10.0.0.22"
PORT = 55000
PORT2 = 5000

addresses = {}
names = {}
files = 'file.txt', 'Sample_file.txt'

class Server:

    def __init__(self):
        while True:
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.bind((HOST, PORT))
                print("Server is running...")
                print(f"Server address --> {HOST}:{PORT}")
                print("Waiting for connection...\n")
                break
            except:
                print("binding failed")
                break

        self.accept_connections()

    def accept_connections(self):
        self.server.listen()
        while True:
            client, address = self.server.accept()
            print("Accepted a connection request from %s:%s" % address)
            addresses[client] = address
            threading.Thread(target=self.handle, args=(client,)).start()

    def handle(self, client):
        name = ""
        while True and client is not None:
            msg = client.recv(1024)
            if msg is not None:
                msg = msg.decode()

            if msg == "":
                msg = "Q#"
            if msg.startswith("ALL#") and name:
                _msg = msg.replace("ALL#", f"MSG#{name}: ")
                self.send_msg(_msg, send_to_everyone=True)
                continue
            if msg.startswith("REG#"):
                name = msg.split('#')[1]
                self.send_msg(f"SYS#welcome {name}", destination=client)
                names[client] = name
                msg2 = client.recv(1024)
                msg2 = msg2.decode()
                if msg2.startswith("JOIN#"):
                    name = msg2.split('#')[1]
                    self.send_msg(f"SYS#{name} has joined the chat.\n", send_to_everyone=True)
                    msg3 = client.recv(1024)
                    msg3 = msg3.decode()
                    if msg3 == "CLI#":
                        self.send_msg(f"CLIENTS#{self.get_names()}", send_to_everyone=True)
                        print(f"--> connected clients: {self.get_names()}")
                continue

            if msg.startswith("FN#"):
                self.send_msg(f"FILES#{self.get_files()}", destination=client)
                continue
            if msg == "Q#":
                client.close()
                try:
                    del names[client]
                except KeyError:
                    pass
                if name:
                    self.send_msg(f"SYS#{name} has left the chat.\n", send_to_everyone=True)
                    time.sleep(0.1)
                    self.send_msg(f"CLIENTS#{self.get_names()}", send_to_everyone=True)
                    print(f"--> connected clients: {self.get_names()}")
                    # print("Accepted a connection request from %s:%s" % address)

                break

            if not name:
                continue
            if msg.startswith("FILE#"):
                udp = threading.Thread(target=send_file, args=(client, msg))
                udp.start()
                continue
            if not msg.startswith("CLI#"):
                try:
                    msg_details = msg.split("#")
                    user = msg_details[0]
                    sock = self.find_sock(user)
                    if sock is not None:
                        self.send_msg(msg_details[1], prefix=name+": ", destination=sock)
                    else:
                        print(f"Invalid Destination. {user}")
                except:
                    print(f"Error parsing the message: {msg}")

    def send_msg(self, msg, send_to_everyone=False, prefix="", destination=None):
        _msg = (prefix + msg)
        if send_to_everyone:
            for sock in names:
                if sock is not None:
                    sock.send(_msg.encode('utf-8'))
        else:
            if destination is not None:
                destination.send(_msg.encode())

    def find_sock(self, name):
        for _sock, _name in names.items():
            if _name == name:
                return _sock
        return None

    def get_names(self, sep=','):
        nicknames = []
        if len(names.items()) == 0:
            return "No one left in chat room"
        for _, name in names.items():
            nicknames.append(name)
        return sep.join(nicknames)

    def get_files(self, sep=','):
        files_names = []
        for file in files:
            files_names.append(file)
        return sep.join(files_names)

def send_file(client, msg):
    seq = 0
    data_buffer = []
    msg_details = msg.split('#')
    filename = msg_details[1]
    username = msg_details[2]
    port = PORT2+len(username)
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, port))
    msg, address = udp_sock.recvfrom(1024)
    print("\n*****************************New request for file*****************************")
    print(f"{msg.decode()}")
    udp_sock.sendto(f"Start Downloading {filename}...".encode(), address)

    msg = udp_sock.recvfrom(1024)[0].decode()
    read = 500

    with open(filename, 'rb', 0) as f:
        while True:
            curr = f.read(read)
            if not curr:
                break
            else:
                currpack = (seq, curr)
                currpack = pickle.dumps(currpack)
                data_buffer.append(currpack)
                seq = seq + 1

    udp_sock.sendto(f'{len(data_buffer)}'.encode(), address)
    print(f"Number of packets to send: {len(data_buffer)}")
    size = len(data_buffer)

    if msg.startswith('START'):
        sending = True
        packet_num = 0
        i = 0
        while sending:
            packet_num = ''
            while i < size:
                time.sleep(0.01)
                udp_sock.settimeout(2)
                try:
                    packet_num = udp_sock.recvfrom(1024)[0].decode()
                    if packet_num != 'FINISH':
                        packet_num = int(packet_num)
                        # data_buffer.pop(packet_num)
                        udp_sock.sendto(data_buffer[packet_num], address)
                    elif packet_num == 'FINISH':
                        i = size
                        sending = False
                except socket.timeout:
                    i += 1
                    pass

        print("******************Finish sending the file******************\n")


if __name__ == '__main__':
    Server()
