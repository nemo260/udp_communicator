import math
import os
import socket
import threading
import time
import zlib

keep_alive = False
stop_thread = False


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


def create_bad_packet(type, data, id, total_packets, bad, good_crc):
    if bad == 0:
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

        return packet, int.from_bytes(packet[7:11], 'big')

    if bad == 1:
        packetID = id
        # total_packets = 2
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(
            3,
            byteorder='big')
        if packetID == 0:
            data = data.encode('utf-8')

        crc = good_crc
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc + data

        return packet


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

    # vytvorenie packetu pre spr??vu
    if type == 2:
        packetID = id
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

    # vytvorenie packetu pre pozitivne ARQ
    if type == 4:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(3,
                                                                                                                    byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet

    # vytvorenie packetu pre negativne ARQ
    if type == 5:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(
            3,
            byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet

    # vytvorenie packetu pre oznamenie ??e nepri??iel packet
    if type == 6:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(
            3,
            byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet

    # vytvorenie packetu pre oznamenie na switchnutie role
    if type == 7:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(
            3,
            byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet

    # vytvorenie keep alive packetu
    if type == 8:
        packetID = 1
        total_packets = 1
        packet = type.to_bytes(1, byteorder='big') + packetID.to_bytes(3, byteorder='big') + total_packets.to_bytes(
            3,
            byteorder='big')
        crc = zlib.crc32(packet)
        crc = crc.to_bytes(4, byteorder='big')
        packet = packet + crc
        return packet


def send_packets(sock, mof):
    global neposkodeny
    global keep_alive
    keep_alive = False
    simulation = False
    packet_lost = False
    pkt_array = []

    if mof == 1:
        data = input("Nap???? spr??vu:\n")
        #packet = create_packet(2, data, 0, 1)

        yn = int(input("Tvoja sprava m?? " + str(len(data)) + " bajtov, chce?? ju deli?? na fragmenty?\nANO - 1\nNIE - 0\n"))

        if yn == 1:
            fragment_size = int(input("Zadaj velkost jedneho fragmentu v bajtoch (max. 1461)\n"))
            wrong_packet = int(input("Chce?? simulova?? chybu?\nPo??le chybn?? packet - 1\nPacket neodo??le - 2\nNechcem "
                                     "simulova?? chybu - 0\n"))

            if wrong_packet == 0:
                pass
            if wrong_packet == 1:
                simulation = True
            if wrong_packet == 2:
                packet_lost = True

            data_size = len(data)
            fragments_num = math.ceil(data_size / fragment_size)

            # vytvori 0-ty packet s nazvom suboru a prida do pola
            packet = create_packet(2, "Message: ", 0, fragments_num)
            pkt_array.append(packet)

            start = 0
            end = fragment_size
            good_pkt_arr = []
            # vytvaranie packetov
            for i in range(1, fragments_num + 1):
                if simulation:  # simuluje prvy packet chybny
                    data_frame = data[start:end]
                    packet, good_crc = create_bad_packet(2, data_frame, i, fragments_num, 0,
                                                         0)  # vytvori dobry packet aj s crc
                    good_pkt_arr.append(packet)

                    data_frame = "smola"
                    packet = create_bad_packet(2, data_frame, i, fragments_num, 1, good_crc)

                    pkt_array.append(packet)
                    start += fragment_size
                    end += fragment_size

                    simulation = False  # vypnutie simulacie pre chybne packety

                else:
                    data_frame = data[start:end]
                    packet = create_packet(2, data_frame, i, fragments_num)
                    pkt_array.append(packet)
                    start += fragment_size
                    end += fragment_size

            # posielanie packetov
            #sock.sendto(pkt_array[0], (ip, udp_port))
            #pkt_array.remove(pkt_array[0])
            for i in range(len(pkt_array)):
                if packet_lost and i != 0 and i == 5:

                    pckt, addr = sock.recvfrom(1500)  # ??aka na sp??tnu v??zbu od servera
                    type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                    if type1 == 6:  # type = 6 - nepri??iel packet na server
                        sock.sendto(pkt_array[i], (ip, udp_port))
                        pckt, addr = sock.recvfrom(1500)
                        type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                        if type1 == 4:
                            print(str(i) + ". packet OK")
                        if type1 == 5:
                            print(str(i) + ". znovu chybny")

                    #packet_lost = False
                else:
                    sock.sendto(pkt_array[i], (ip, udp_port))
                    pckt, addr = sock.recvfrom(1500)  # ??aka na sp??tnu v??zbu od servera
                    type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                    if type1 == 4:
                        print(str(i) + ". packet OK")
                    if type1 == 5:
                        sock.sendto(good_pkt_arr[0], (ip, udp_port))
                        del good_pkt_arr[0]
                        pckt, addr = sock.recvfrom(1500)  # ??aka na sp??tnu v??zbu od servera
                        type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                        if type1 == 4:
                            print(str(i) + ". packet OK")
                        if type1 == 5:
                            print(str(i) + ". znovu chybny")
                    #packet_lost = True
            print("Odoslalo sa " + str(fragments_num) + " fragmentov")
            print()

        if yn == 0:
            packet = create_packet(2, "Message: ", 0, 2)
            pkt_array.append(packet)

            packet = create_packet(2, data, 1, 2)
            pkt_array.append(packet)

            for i in range(len(pkt_array)):
                sock.sendto(pkt_array[i], (ip, udp_port))

    if mof == 2:
        path = input("Zadaj cestu k s??boru: ")
        #path = "D:/skola/3.sem/pks/2zadanie/crc.jpg"
        f = open(path, "rb")
        data = f.read()

        save_file = input(
            "Zadaj absolutnu cestu k suboru kde ma by?? ulo??en?? (Ak nechce?? stla?? 0 a ulo???? to tam kde je program): ")

        yn = int(input("Tvoj s??bor m?? " + str(len(data)) + " bajtov, chce?? ho deli?? na fragmenty?\nANO - 1\nNIE - 0\n"))
        if yn == 0 and len(data) > 1461:
            print("Tvoj s??bor m?? " + str(len(data)) + " bajtov, je potrebne ho rozdeli?? na fragmenty!")
            yn = 1

        if yn == 1:
            fragment_size = int(input("Zadaj velkost jedneho fragmentu v bajtoch (max. 1461)\n"))
            wrong_packet = int(input("Chce?? simulova?? chybu?\nPo??le chybn?? packet - 1\nPacket neodo??le - 2\nNechcem "
                                     "simulova?? chybu - 0\n"))

            if wrong_packet == 0:
                pass
            if wrong_packet == 1:
                simulation = True
            if wrong_packet == 2:
                packet_lost = True

            data_size = len(data)
            fragments_num = math.ceil(data_size / fragment_size)

            # vytvori 0-ty packet s nazvom suboru a prida do pola
            if save_file == "0":
                packet = create_packet(3, "D:/skola/pks 2 zadanie/pks2_zadanie/" + os.path.basename(path), 0,
                                       fragments_num)
            else:
                packet = create_packet(3, save_file + os.path.basename(path), 0, fragments_num)
            pkt_array.append(packet)

            start = 0
            end = fragment_size
            good_pkt_arr = []
            # vytvaranie packetov
            for i in range(1, fragments_num + 1):
                if simulation:  # simuluje prvy packet chybny
                    data_frame = data[start:end]
                    packet, good_crc = create_bad_packet(3, data_frame, i, fragments_num, 0,
                                                         0)  # vytvori dobry packet aj s crc
                    good_pkt_arr.append(packet)

                    data_frame = b"smola"
                    packet = create_bad_packet(3, data_frame, i, fragments_num, 1, good_crc)

                    pkt_array.append(packet)
                    start += fragment_size
                    end += fragment_size

                    simulation = False  # vypnutie simulacie pre chybne packety

                else:
                    data_frame = data[start:end]
                    packet = create_packet(3, data_frame, i, fragments_num)
                    pkt_array.append(packet)
                    start += fragment_size
                    end += fragment_size

            # posielanie packetov

            for i in range(len(pkt_array)):
                if packet_lost and i == 22:

                    pckt, addr = sock.recvfrom(1500)  # ??aka na sp??tnu v??zbu od servera
                    type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                    if type1 == 6:  # type = 6 - nepri??iel packet na server
                        sock.sendto(pkt_array[i], (ip, udp_port))
                        pckt, addr = sock.recvfrom(1500)
                        type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                        if type1 == 4:
                            print(str(i) + ". packet OK")
                        if type1 == 5:
                            print(str(i) + ". znovu chybny")

                    # packet_lost = False
                else:
                    sock.sendto(pkt_array[i], (ip, udp_port))
                    pckt, addr = sock.recvfrom(1500)  # ??aka na sp??tnu v??zbu od servera
                    type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                    if type1 == 4:
                        print(str(i) + ". packet OK")
                    if type1 == 5:
                        sock.sendto(good_pkt_arr[0], (ip, udp_port))
                        del good_pkt_arr[0]
                        pckt, addr = sock.recvfrom(1500)  # ??aka na sp??tnu v??zbu od servera
                        type1, packetID1, total_packets1, crc1, data1 = decode_packet(pckt)
                        if type1 == 4:
                            print(str(i) + ". packet OK")
                        if type1 == 5:
                            print(str(i) + ". znovu chybny")
            print("Odoslalo sa " + str(fragments_num) + " fragmentov o velkosti " + str(fragment_size) + " bajtov.")
            print("Absolutna cesta k suboru: " + path)
            print("Nazov s??boru: " + os.path.basename(path))
            print()

        if yn == 0:
            packet = create_packet(3, os.path.basename(f.name), 0, 2)
            pkt_array.append(packet)

            packet = create_packet(3, data, 1, 2)
            pkt_array.append(packet)

            for i in range(len(pkt_array)):
                sock.sendto(pkt_array[i], (ip, udp_port))

        f.close()


def keep_alive_function(sock, ip):
    while True:
        if stop_thread:
            break
        if keep_alive:
            time.sleep(5)
            packet = create_packet(8, "", 0, 1)
            sock.sendto(packet, (ip, udp_port))


def client(sock):
    global keep_alive
    global stop_thread
    keep_alive = True
    message_or_file = int(input("Posla?? spr??vu - 1\nPosla?? subor - 2\nMenu - 0\n"))
    if message_or_file == 0:
        keep_alive = False
        stop_thread = True
        starting("client", sock, ip)

    else:
        send_packets(sock, message_or_file)
        client(sock)


def client_mode():
    print("Toto zariadenie je pou????van?? ako CLIENT\n")
    global ip
    global udp_port
    global keep_alive
    global stop_thread
    stop_thread = False
    ip = input("Zadaj IP kam chce?? posiela?? s??bory: ")
    udp_port = int(input("Zadaj port: "))

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

    t1 = threading.Thread(target=keep_alive_function, args=(sock, ip))
    t1.start()
    client(sock)


def crc_is_good(pckt, crc):
    pkt_no_crc = pckt[0:7] + pckt[11:]
    crc_new = zlib.crc32(pkt_no_crc)
    if crc_new == crc:
        return True
    else:
        return False


def catch_packets(sock, ip):
    counter = 0
    pkt_arr = []
    cesta = ""
    timer = False
    sock.settimeout(30)
    try:
        # cyklus pre prijmanie packetov
        while True:

            if timer:
                sock.settimeout(3)
            try:
                pckt, addr = sock.recvfrom(1500)
                type, packetID, total_packets, crc, data = decode_packet(pckt)
                if packetID == 0:
                    timer = True

                if type == 7:
                    sock.close()
                    client_mode()

                if type == 8:
                    print("Keep alive pkt")
                    timer = False
                    catch_packets(sock, ip)

                if crc_is_good(pckt, crc):
                    print("Packet " + str(packetID) + ": OK")
                    packet = create_packet(4, "", 0, 1)  # odoslanie spravy ??e packet do??iel OK
                    sock.sendto(packet, (addr[0], udp_port))
                    # pokracovanie zistovania pcketov
                    if type == 2:
                        if packetID == 0:
                            pkt_arr = []
                            pass
                        else:
                            counter += 1
                            pkt_arr.append(data)

                            if counter == total_packets:
                                print("Prijata sprava: ", end="")
                                for i in pkt_arr:
                                    print(i, end="")
                                print()
                                timer = False
                                catch_packets(sock, ip)
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
                                print("S??bor " + os.path.basename(cesta) + " prijat??. Cesta k s??boru: " + os.path.abspath(
                                    cesta))
                                print("Prijat??ch " + str(total_packets) + " fragmentov. Velkos?? s??boru v bajtoch: " + str(
                                    os.path.getsize(cesta)))
                                print()
                                timer = False
                                catch_packets(sock, ip)



                else:
                    print("Packet " + str(packetID) + ": ZLY PACKET")
                    packet = create_packet(5, "", 0, 1)  # odoslanie spravy ??e do??iel zly packet
                    sock.sendto(packet, (addr[0], udp_port))
            except:
                if timer:
                    print("Packet " + str(counter + 1) + ": LOST")
                    packet = create_packet(6, "", 0, 1)  # odoslanie spravy ??e nedo??iel packet
                    sock.sendto(packet, (ip, udp_port))
                    # catch_packets(sock, ip)
    except:
        print("Neprebieha komunikacia ani keep alive.")
        print("Program sa vypne...")
        exit()


def server_mode(communication, sock):
    global f
    global ip
    if communication:
        catch_packets(sock, ip)
    else:
        print("Toto zariadenie je pou????van?? ako SERVER\n")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(30)
        # nadviazanie komunikacie
        try:
            sock.bind((my_ip, udp_port))
            pckt, addr = sock.recvfrom(1500)
            type, packetID, total_packets, crc, data = decode_packet(pckt)

            if type == 0:
                print("Nadviazane spojenie s " + str(addr[0]))
                packet = create_packet(1, "", 0, 1)
                sock.sendto(packet, (addr[0], udp_port))
                ip = addr[0]
                communication = True
                server_mode(communication, sock)
        except:
            sock.close()
            print("Vyprsal cas")


def starting(role, sock, ip):
    option = int(input("Client mode - 1\nServer mode - 2\nExit - 0\n"))
    if option == 1:
        client_mode()
    if option == 2:
        if role == "client":
            packet = create_packet(7, "", 0, 1)
            sock.sendto(packet, (ip, udp_port))
            sock.close()
            server_mode(False, 0)
        else:
            server_mode(communication, 0)
    if option == 0:
        exit()


my_ip = socket.gethostbyname(socket.gethostname())
udp_port = 5005
communication = False

print("Program starting...")
print("This PC IP address: " + my_ip)

starting(0, 0, 0)
