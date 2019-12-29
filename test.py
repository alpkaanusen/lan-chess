import socket, time, threading, chess
import chess_engine

connected_hosts = []
connected_ips = []
playing = False
kill_threads = False #used to terminate background threads 
announce_lock = False # used to start another round of announcement messages after the previous one is completed
#this is a workaround, but I could not get any other solution working
#opens a socket to google.com, gets the ip address from that connection and closes it without sending anything
tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tmp.connect(("8.8.8.8", 80))
IP = tmp.getsockname()[0]
tmp.close()
PORT = 12345
BUFFER_SIZE = 1500
NAME = 'Alp Kaan Usen'
 
ANNOUNCE_PACKET = ('[%s, %s, announce]' % (NAME, IP))
RESPONSE_PACKET = ('[%s, %s, response]' % (NAME, IP))

def announce():
    announce_lock = True #do not allow another round to start
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP message
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        s.settimeout(1)
        s.sendto(str.encode(ANNOUNCE_PACKET), ('<broadcast>', PORT))
    except:
    	s.close()
    s.close()
    announce_lock = False
    
def response_tcp():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP,PORT))
    s.listen(5)
    while True and not kill_threads:
        conn, addr = s.accept()
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
                if not data: 
                    break
                message = data.decode()
                message = message[1:len(message)-1] # remove brackets
                message = message.replace(", ", ",") #remove whitespace
                message = message.split(",")
                #conn.send(str.encode(RESPONSE_PACKET))
                global playing
                if message[2] == 'invite' and not playing:
                    answer = ''
                    while answer != 'a' and answer != 'r':
                        answer = input(message[0] + " invites you to a game of chess, (A)ccept or (R)eject: ").lower()
                    if answer == 'a':
                        connected = send_answer(message[1], 'accept')
                        if connected:
                            playing = True
                            start_game(chess.BLACK)
                        else:
                            print("could not connect")
                    else:
                        send_message(message[1], 'reject')
                elif message[2] == "accept":
                    send_answer(message[1], 'received')
                    print("Starting game with " + host_name)
                    start_game(chess.WHITE)
                elif response[2] == "reject":
                    send_answer(message[1], 'received')
                    print(host_name + " rejected your invite")
                    print()
                elif message[2] == 'move':
                    print()
            except Exception as e:
                print (str(e))
                break
        conn.close()
    s.close()

def response_udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('',PORT))
    while True and not kill_threads:
        while True:
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
                if not data: 
                    break
                message = data.decode()
                message = message[1:len(message)-1] # remove brackets
                message = message.replace(", ", ",") #remove whitespace
                message = message.split(",")
                if message[1] == IP:
                    break
                if message[2] == 'announce' and message[1] not in connected_ips:
                    connected_hosts.append((message[0], message[1])) #get name and ip
                    connected_ips.append(message[1])
                    #send response, try 3 times for safety
                    for _ in range(0,3):
                        s.sendto(str.encode(RESPONSE_PACKET), (message[1], PORT))
                elif message[2] == 'response' and message[1] not in connected_ips:
                    connected_hosts.append((message[0], message[1])) #get name and ip
                    connected_ips.append(message[1])
            except Exception as e:
                print (str(e))
                break
    s.close()
 
def send_answer(host_ip, answer):
    MESSAGE_PACKET = ('[%s, %s, %s]' % (NAME, IP, answer))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(5)
        s.connect((host_ip, PORT))
        s.send(str.encode(MESSAGE_PACKET))
        while True:
            data = s.recv(BUFFER_SIZE)
            if data:
                break
        response = data.decode()
        response = response[1:len(response)-1] # remove brackets
        response = response.replace(" ", "")
        response = response.split(",")
        print(response)
        if response[2] == "received" and answer == 'accept':
            return True
        else:
            return False
    except Exception as e:
        print("Error sending the message, try again: " + str(e))
    s.close()

def send_invite(host_name, host_ip):
    MESSAGE_PACKET = ('[%s, %s, invite]' % (NAME, IP))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(30)
        s.connect((host_ip, PORT))
        s.send(str.encode(MESSAGE_PACKET))
        '''
        while True:
            data = s.recv(BUFFER_SIZE)
            if data:
                break
        response = data.decode()
        response = response[1:len(response)-1] # remove brackets
        response = response.replace(" ", "")
        response = response.split(",")
        print(response)
        if response[2] == "accept":
            send_answer(message[1], 'received')
            print("Starting game with " + host_name)
            start_game(chess.WHITE)
        elif response[2] == "reject":
            send_answer(message[1], 'received')
            print(host_name + " rejected your invite")
            print()
        '''
    except Exception as e:
        print("Error connecting, try again: " + str(e))
    s.close()

def print_connected_hosts():
    if len(connected_hosts) == 0:
        print("No one is currently online")
    else:	
        print("Online players: ")
        for host in connected_hosts:
            i = 0
            print(str(i) + ". " + host[0] + " - " + host[1])
            i += 1
    print()
def start_game(color):
    print("starting game")

def sendMove():
    print()

if __name__ == '__main__':
    #response threads always runs on background
    response_tcp_thread = threading.Thread(target=response_tcp)
    response_tcp_thread.start()
    response_udp_thread = threading.Thread(target=response_udp)
    response_udp_thread.start()
    #announce 3 times on startup
    for i in range(0,3):
        while announce_lock:
            continue #wait while the first round finishes
        announce()
    while True:
        try:
            host_index = int(input("Choose player to invite to a game of chess(-1 to see online players, -2 to exit): "))
            if host_index == -2:
                print("exiting")
                kill_threads = True
                response_tcp_thread.join()
                response_udp_thread.join()
                exit()
            elif host_index == -1:
                print_connected_hosts()
            elif host_index < len(connected_hosts) and host_index >= 0:
                print("Sending invite to: " + connected_hosts[host_index][0])
                send_invite(connected_hosts[host_index][0], connected_hosts[host_index][1])
        except Exception as e:
            print("Please enter an integer: " + str(e))