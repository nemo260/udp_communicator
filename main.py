import socket
import threading
import time


def recieving(sock):
    sock.bind((udp_ip, udp_port))
    while True:
        data, addr = sock.recvfrom(1024)
        print("Recieved message: " + data)


def send_message():
    message = input("Write your message: \n")
    message = bytes(message, "utf-8")
    sock.sendto(message, (udp_ip, udp_port))
    print("Message: [" + str(message) + "] was send")


def client_mode():
    print("!!! Program is running as a Client !!!")
    time.sleep(1)
    while True:
        print()
        message_or_file = int(input(
            "If you want to send message, press 0\nIf you want to send file, press 1\nIf you want to change mode, press 2\n"))
        if message_or_file == 0:
            send_message()
        if message_or_file == 2:
            starting()


def server_mode():
    print("!!! Program is running as a Server !!!")
    time.sleep(1)

    recieving(sock)
    print()
    message_or_file = int(input("If you want to recieving, press 0\nIf you want to change mode, press 2\n"))
    if message_or_file == 0:
       recieving(sock)
    if message_or_file == 2:
       starting()


def starting():
    option = int(input("Press 0 for Client mode or press 1 for Server mode\n"))
    if option == 0:
        client_mode()
    if option == 1:
        server_mode()


udp_ip = "192.168.0.104"
udp_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("Program starting...")
time.sleep(1)
starting()
