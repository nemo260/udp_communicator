import socket
import threading

""""
def recieving(sock):
    sock.bind((udp_ip, udp_port))
    while True:
        data, addr = sock.recvfrom(1024)
        print("recieved message: " + data)
"""

udp_ip = "10.0.2.15"
udp_port = 5000


"""
t1 = threading.Thread(target=recieving(sock), name="t1")
t1.start()
"""
message = b"Hello kokot"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(message, (udp_ip, udp_port))
