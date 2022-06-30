import pickle
import socket
import threading
import time
import tkinter as tk
from tkinter import *
import tkinter.scrolledtext
from tkinter import ttk, simpledialog

# HOST = "192.168.1.206"
# PORT = 55000
NUM = 6

class Client:

    def __init__(self, user_name, cli_ip, cli_port):
        self.name = user_name
        self.ip = cli_ip
        self.port = cli_port
        self.port2 = 5000+len(user_name)
        self.connected = False
        self.sock = socket.socket()
        self.connect(self.ip, self.port)
        self.gui_done = False

        self.count = 0
        self.chat_tab = tk.Tk()
        self.chat_tab.configure(bg="lightgrey")
        self.chat_tab.title(f"Chat Room: {self.name}")

        self.chat = tk.scrolledtext.ScrolledText(self.chat_tab, height=3*NUM, width=8*NUM)
        self.chat.config(state="disabled")
        self.chat.tag_config('msg', foreground='#2916d9')
        self.chat.tag_config('sys', foreground='black')
        self.chat.tag_config('private', foreground='#cc21b2')
        self.files_list = ['Please choose a file']

        self.friend_list = tk.Listbox(self.chat_tab, height=2*NUM, width=3*NUM)
        self.files_combobox = ttk.Combobox(self.chat_tab, width=3*NUM, state='readonly')
        self.files_combobox['values'] = self.files_list
        self.files_combobox.current(0)
        self.files_combobox.bind('<<ComboboxSelected>>', self.send_filename)

        self.list = ["ALL"]
        self.clicked = tk.StringVar(self.chat_tab)
        self.clicked.set(self.list[0])
        self.file_clicked = tk.StringVar(self.chat_tab)
        self.file_clicked.set(self.files_list[0])

        self.combobox = ttk.Combobox(self.chat_tab, width=2*NUM, state='readonly')
        self.combobox['values'] = self.list
        self.combobox.current(0)
        self.clicked = self.combobox.get()
        self.combobox.bind('<<ComboboxSelected>>', self.send_choice)

        self.sendto_txt = tk.Label(self.chat_tab, text="Send to: ALL")
        self.input = tk.Entry(self.chat_tab, width=6*NUM, bd=NUM)
        self.input.config(font=("Ariel", 12))
        self.input.bind('<Return>', self.enter_line)
        self.send_btn = tk.Button(self.chat_tab, text="Send", width=NUM, command=self.enter_line)
        self.disconnect_btn = tk.Button(self.chat_tab, text="Disconnect",  width=2*NUM, command=self.disconnect)
        self.file_btn = tk.Button(self.chat_tab, text="Download", width=2*NUM, command=self.get_file)
        # Grid
        self.chat.grid(row=0, column=0)  ### columnspan=2)
        self.disconnect_btn.grid(row=0, column=1, padx=2, sticky='N')
        self.friend_list.grid(row=0, column=1, padx=2)

        self.sendto_txt.grid(row=1, column=0,  pady=2,  padx=20, sticky="W")
        self.combobox.grid(row=1, column=0) #, padx=50)

        self.files_combobox.grid(row=1, column=1, padx=2)

        self.input.grid(row=2, column=0, padx=2, sticky="W")
        self.send_btn.grid(row=2, column=0, padx=2, sticky="E")

        self.file_btn.grid(row=2, column=1, padx=2)

        self.gui_done = True
        self.chat_tab.protocol("WM_DELETE_WINDOW", self.disconnect)
        self.chat_tab.mainloop()

        # Function of getting the file from the server
    def stop_downloading(self):
        pass

    def get_file(self):
        self.sock.sendto(f"FILE#{self.file_clicked}#{self.name}".encode(), (self.ip, self.port2))
        packet_lost = []  # Stores lost packets
        UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Starting UDP Connection
        time.sleep(0.5)
        UDP_socket.sendto(f"{self.name} want to download the file: {self.file_clicked}".encode(), (self.ip, self.port2))  # Sending first message to the Server
        msg = UDP_socket.recvfrom(1024)[0]  # Waiting for connection aproval
        print(msg.decode())
        UDP_socket.sendto("START".encode(), (self.ip, self.port2)) # Saying to the server to start transfer the file
        packets = UDP_socket.recvfrom(1024)[0]  # Reciving the number of packet the server would send to the client
        packets = packets.decode()
        num_pack = int(packets)
        print(f"Num of packets: {num_pack}")
        receiving = True
        received_packets =  [] # Stores packets
        while receiving:  # Starting the receiving loop
            packet_lost = []
            i = 0
            while i < num_pack:
                UDP_socket.settimeout(2)
                UDP_socket.sendto(f'{i}'.encode(),(self.ip, self.port2))
                UDP_socket.settimeout(2)
                try:
                    data = UDP_socket.recvfrom(1024)[0]  # Getting the packets from the server
                    data = pickle.loads(data)

                    if i == data[0]:  # For packets that got lost
                        print(data[0])
                        received_packets.insert(data[0], data[1])

                        time.sleep(0.05)

                    else:
                        received_packets.insert(data[0],data[1])
                        print(data[0])
                        UDP_socket.sendto(f'{data[0]}'.encode(),(self.ip, self.port2))
                        time.sleep(0.05)
                    i += 1
                except socket.timeout:
                    # No packet
                    packet_lost.append(f'{i}')
                    print(f"******************packet number {i}******************")
                    i += 1
                    pass
            print(f"packet lost: {len(packet_lost)}")
            size = len(packet_lost)

            while size > 0:
                i = 0
                size = len(packet_lost)
                while i < size:
                        # print(f"asking for {packet_lost[i]} in {i}")
                        UDP_socket.sendto(f'{packet_lost[i]}'.encode(),(self.ip, self.port2))
                        UDP_socket.settimeout(2)
                        # print(i)
                        try:
                            data = UDP_socket.recvfrom(1024)[0]  # Getting the packets from the server
                            data = pickle.loads(data)
                            print(data[0])
                            received_packets.insert(data[0], data[1])
                            packet_lost.pop(i)
                            size -= 1
                            print(f"size: {size}")
                            time.sleep(0.01)

                        except socket.timeout:
                            # No packet
                            i += 1
                            # print(f"******************packet number {packet_lost[i]}******************")
                            pass
            UDP_socket.sendto(f'FINISH'.encode(),(self.ip, self.port2))


            with open(self.file_clicked.split('.')[0] + f'{self.count}.' + self.file_clicked.split('.')[1], 'wb',0) as fwrite:  # Saving the file.
                for num in range(0, len(received_packets)):
                    fwrite.write(received_packets[num])
            receiving = False
            print("Finish downloading the file")
            self.count += 1


    def connect(self, ip, port):
        address = ip, port

        if self.connected:
            return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(address)
            print("successfully connected to: %s:%s" % address)
        except:
            self.sock = socket.socket()
            return
        self.sock.send(f"REG#{self.name}".encode())
        self.connected = True

        self.update_thread = threading.Thread(target=self.update_room).start()

    def disconnect(self):
        if not self.connected:
            return
        q = 'Q#'
        self.sock.send(q.encode())
        self.connected = False
        # self.sock = socket.socket()
        self.sock.close()
        self.stop()

    def stop(self):
        self.chat_tab.destroy()
        exit(0)

    def enter_line(self, event=None):
        line = f"{self.input.get()}"
        if not line.strip():
            return
        if self.clicked != "ALL":
            self.sock.send(f"{self.name}#{line}\n".encode())
            time.sleep(0.1)
        self.sock.send(f"{self.clicked}#{line}\n".encode())
        time.sleep(0.1)
        self.input.delete(0, END)

    def receive(self, msg, color):
        while self.connected:
            try:
                if msg != "":
                    if self.gui_done:
                        self.chat.config(state='normal')
                        self.chat.insert('end', msg, color)
                        self.chat.yview('end')
                        self.chat.config(state='disabled')
                        break
            except ConnectionAbortedError:
                break
            except:
                print("Error")
                self.sock.close()
                break

    def update_room(self):
        while self.connected:
            data = self.sock.recv(1024)
            data = data.decode()
            if data != "":

                if data[:11] == "SYS#welcome":
                    self.receive(f"{data[4:]}!\n", 'sys')
                    msg = f"JOIN#{data[12:]}"
                    self.sock.send(msg.encode())

                elif data[:4] == "SYS#":
                    # if self.name not in data[4:]:
                    self.receive(data[4:], 'sys')
                    msg = "CLI#"
                    self.sock.send(msg.encode())

                elif data[:8] == "CLIENTS#":
                    clients_list = data.split("CLIENTS#")
                    self.update_combobox(clients_list[1])
                    self.update_members_list(clients_list[1])
                    msg = "FN#"
                    self.sock.send(msg.encode())

                elif data[:6] == "FILES#":
                    self.update_files(data[6:])

                elif data[:4] == "MSG#":
                    self.receive(data[4:], 'msg')

                else:
                    data_details = data.split(":")
                    if data_details[0] == self.name:
                        self.receive(f"{data_details[0]} -> {self.clicked}:{data_details[1]}", 'private')
                    else:
                        self.receive(f"{data_details[0]} -> {self.name}:{data_details[1]}", 'private')

            time.sleep(0.1)

    def update_members_list(self, members_list):
        mem_list = members_list.split(",")
        self.friend_list.delete(0, 'end')
        for member in mem_list:
            self.friend_list.insert(END, member)

    def update_files(self, files_list):
        fs = files_list.split(",")
        self.files_combobox.set('')
        self.files_list.clear()
        for file in fs:
            self.files_list.insert(0, file)

        self.files_combobox['values'] = self.files_list
        index = self.files_combobox.current()
        if index != -1:
            self.files_combobox.current(index)
        else:
            self.files_combobox.current(0)
            self.send_filename()

    def update_combobox(self, members_list):
        mem_list = members_list.split(",")
        self.combobox.set('')
        self.list.clear()
        self.list.insert(0, "ALL")
        for member in mem_list:
            if member != self.name:
                self.list.insert(1, member)

        self.combobox['values'] = self.list
        print(self.list)
        index = self.combobox.current()
        if index != -1:
            self.combobox.current(index)
        else:
            self.combobox.current(0)
            self.send_choice()

    def send_filename(self, event=None):
        self.file_clicked = self.files_combobox.get()

    def send_choice(self, event=None):
        self.clicked = self.combobox.get()
        self.sendto_txt.config(text=f"Send to: {self.combobox.get()}")


if __name__ == '__main__':

    win = tk.Tk()
    win.withdraw()
    sd = tk.simpledialog
    name = sd.askstring("Your name", "What is your name", parent=win)
    if name.strip():
        ip_entry = sd.askstring("IP", "IP: ", initialvalue='192.168.1.206', parent=win)
        # ip_entry = sd.askstring("IP", "IP: ", initialvalue='10.42.0.1', parent=win)
        # ip_entry = sd.askstring("IP", "IP: ", initialvalue='127.0.0.1', parent=win)

        # ip_entry = '127.0.1.1'
        # ip_entry = '192.168.1.108'
        # ip_entry = '10.0.0.22'

        if ip_entry.strip():
            # port_entry = 55000
            port_entry = sd.askinteger("PORT", "PORT: ", initialvalue=55000, parent=win)
            if port_entry is not None:
                Client(name, ip_entry, port_entry)