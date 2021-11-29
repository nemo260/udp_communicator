import socket
import threading
import time


def recieving(sock):
    sock.bind((udp_ip, udp_port))
    while True:
        data, addr = sock.recvfrom(1500)
        print("Recieved message: " + data)


#
#
# """
# t1 = threading.Thread(target=recieving(sock), name="t1")
# t1.start()
# """
#
# message = "Dobar dan"
# message = bytes(message, "utf-8")
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
# sock.sendto(message, (udp_ip, udp_port))

def send_message(sock):
    message = input("Write your message: \n")
    message = bytes(message, "utf-8")
    sock.sendto(message, (udp_ip, udp_port))
    print("Message: [" + str(message) + "] was send")

def client_mode():
    print("Program is running as a Client...")
    time.sleep(1)
    print("**********************************")
    message_or_file = int(input("If you want to send message, press 0\nIf you want to send file, press 1\n"))
    if message_or_file == 0:
        send_message(sock)

def server_mode():
    print("Program is running as a Server...")
    time.sleep(1)
    print("Program is waiting for communication...")

    recieving(sock)


def starting():
    while True:
        try:
            option = int(input("Press 0 for Client mode or press 1 for Server mode\n"))
            if option == 0:
                client_mode()
            if option == 1:
                server_mode()
        except:
            print("Bad input")


udp_ip = "192.168.0.104"
udp_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("Program starting...")
time.sleep(0.5)
starting()
