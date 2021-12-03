import random
import socket
import threading
import time
import zlib
import os
import math


def decode_packet(pkt):
    type = int.from_bytes(pkt[0:1], 'big')
    packetID = int.from_bytes(pkt[1:4], 'big')
    total_packets = int.from_bytes(pkt[4:7], 'big')
    crc = int.from_bytes(pkt[7:11], 'big')
    # data = pkt[11:].decode('utf-8')
    data = ""
    if type == 2:
        data = pkt[11:].decode('utf-8')
    if type == 3:
        data = pkt[11:]

    return type, packetID, total_packets, crc, data


def create_packet(type, data, id, total_packets):
    if type == 0:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(3,
                                                                                                                    byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet

    if type == 1:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(3,
                                                                                                                    byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet

    # vytvorenie packetu pre správu
    if type == 2:
        packetID = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(3,
                                                                                                                    byteorder='big')
        data = data.encode('utf-8')
        crc = zlib.crc32(packet + data)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc + data

        return packet

    # vytvorenie packetu pre subor
    if type == 3:
        packetID = id
        # total_packets = 2
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(
            3,
            byteorder='big')
        if packetID == 0:
            data = data.encode('utf-8')

        crc = zlib.crc32(packet + data)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc + data

        return packet


def send_packets(sock, mof):
    pkt_array = []
    if mof == 1:
        msg = input("Napíš správu:\n")
        packet = create_packet(2, msg, 0, 1)
        sock.sendto(packet, (ip, udp_port))

    if mof == 2:
        # path = input("Zadaj cestu k súboru: ")
        path = "D:/skola/3.sem/pks/2zadanie/7207.jpg"
        f = open(path, "rb")
        data = f.read()
        yn = int(input("Tvoj súbor má " + str(len(data)) + " bajtov, chceš ho deliť na fragmenty?\nANO - 1\nNIE - 0\n"))
        if yn == 0 and len(data) > 1461:
            print("Maximalna velkost dat v jednom fragmente je 1461 bajtov, program to rozdelí za teba.")

            data_size = len(data)
            fragmets_num = math.ceil(data_size / 1460)

            # vytvori 0-ty packet s nazvom suboru a prida do pola
            packet = create_packet(3, os.path.basename(f.name), 0, fragmets_num)
            pkt_array.append(packet)

            start = 0
            end = 1460
            for i in range(1, fragmets_num + 1):
                data_frame = data[start:end]
                packet = create_packet(3, data_frame, i, fragmets_num)
                pkt_array.append(packet)
                start += 1460
                end += 1460

            for i in range(len(pkt_array)):
                sock.sendto(pkt_array[i], (ip, udp_port))

        if yn == 1:
            fragment_size = int(input("Zadaj velkost jedneho fragmentu v bajtoch\n"))
            data_size = len(data)
            fragments_num = math.ceil(data_size / fragment_size)

            # vytvori 0-ty packet s nazvom suboru a prida do pola
            packet = create_packet(3, os.path.basename(f.name), 0, fragments_num)
            pkt_array.append(packet)

            start = 0
            end = fragment_size
            k = 1
            for i in range(1, fragments_num + 1):
                data_frame = data[start:end]
                packet = create_packet(3, data_frame, i, fragments_num)
                pkt_array.append(packet)
                start += fragment_size
                end += fragment_size

            for i in range(len(pkt_array)):
                if i == 8 * k:
                    time.sleep(0.1)
                    k += 1
                sock.sendto(pkt_array[i], (ip, udp_port))

        if yn == 0:
            packet = create_packet(3, os.path.basename(f.name), 0, 2)
            pkt_array.append(packet)

            packet = create_packet(3, data, 1, 2)
            pkt_array.append(packet)

            for i in range(len(pkt_array)):
                sock.sendto(pkt_array[i], (ip, udp_port))

        f.close()


def client(sock):
    message_or_file = int(input("Poslať správu - 1\nPoslať subor - 2\nMenu - 0\n"))
    if message_or_file == 0:
        starting()
    send_packets(sock, message_or_file)
    client(sock)


def client_mode():
    print("Toto zariadenie je používané ako CLIENT\n")
    global ip
    ip = input("Type IP address where you want to send files: ")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = create_packet(0, "", 0, 1)
    sock.sendto(packet, (ip, udp_port))
    sock.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(30)
    try:
        sock.bind((my_ip, udp_port))
        pckt, addr = sock.recvfrom(1500)
        type, packetID, total_packets, crc, data = decode_packet(pckt)

        if type == 1:
            print("Nadviazane spojenie s " + str(addr[0]))
    except:
        sock.close()
        print("Vyprsal cas")

    client(sock)


def server_mode():
    global f
    cesta = ""
    pkt_arr = []
    counter = 0
    print("Toto zariadenie je používané ako SERVER\n")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(30)
    try:
        sock.bind((my_ip, udp_port))
        pckt, addr = sock.recvfrom(1500)
        type, packetID, total_packets, crc, data = decode_packet(pckt)

        if type == 0:
            print("Nadviazane spojenie s " + str(addr[0]))
            packet = create_packet(1, "", 0, 1)
            sock.sendto(packet, (addr[0], udp_port))
    except:
        sock.close()
        print("Vyprsal cas")

    while True:
        pckt, addr = sock.recvfrom(1500)
        type, packetID, total_packets, crc, data = decode_packet(pckt)
        if type == 2:
            print("Prijata sprava od " + str(addr[0]) + ": " + data)
        if type == 3:
            if packetID == 0:
                pkt_arr = []
                f = open(data, "wb")
                cesta = data.decode('utf-8')

                f.close()
            else:
                counter += 1
                pkt_arr.append(data)

                if counter == total_packets:
                    f = open(cesta, "wb")
                    for i in range(total_packets):
                        f.write(pkt_arr[i])
                    f.close()
                    print("Súbor bol prijatý. Cesta k súboru: " + os.path.abspath(cesta))

def starting():
    option = int(input("Client mode - 1\nServer mode - 2\nExit - 0\n"))
    if option == 1:
        client_mode()
    if option == 2:
        server_mode()
    if option == 0:
        exit()


my_ip = socket.gethostbyname(socket.gethostname())
udp_port = 5005

print("Program starting...")
print("This PC IP address: " + my_ip)

starting()
