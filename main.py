import socket, time, threading, chess
from chess_engine import ChessGame
import sys
import chess.svg
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox

connected_hosts = []
connected_ips = []
playing = False # true when in game
color = False # chess.WHITE = True , chess.BLACK = False
game = None #to access the game object from main.py
connected_ip = '' #ip of the player which is currently being played against
waiting_answer = False # true when an invite is sent and the answer is not yet received

announce_lock = False # used to start another round of announcement messages after the previous one is completed

#this is a workaround, but I could not get any other solution working
#opens a socket to google.com, gets the ip address from that connection and closes it without sending anything
tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tmp.connect(("8.8.8.8", 80))
IP = tmp.getsockname()[0]
tmp.close()

TCP_PORT = 5000
UDP_PORT = 3000
BUFFER_SIZE = 1500
NAME = ''
 
ANNOUNCE_PACKET = ('[%s, %s, announce]' % (NAME, IP))
RESPONSE_PACKET = ('[%s, %s, response]' % (NAME, IP))

def announce():
    announce_lock = True #do not allow another round to start
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP message
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        s.settimeout(1)
        s.sendto(str.encode(ANNOUNCE_PACKET), ('<broadcast>', UDP_PORT))
    except:
    	s.close()
    s.close()
    announce_lock = False
    
def response_tcp():
    global connected_ip
    global game
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP,TCP_PORT))
    s.listen(5)
    while True:
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
                global color
                if message[2] == 'invite' and not playing:
                    answer = ''
                    while answer != 'a' and answer != 'r':
                        answer = input(message[0] + " invites you to a game of chess, (A)ccept or (R)eject: ").lower()
                    if answer == 'a':
                        send_answer(message[1], 'accept')
                    else:
                        send_message(message[1], 'reject')
                elif message[2] == "accept":
                    send_answer(message[1], 'received_accept')
                    print("Starting game with " + message[0])
                    print()
                    color = chess.WHITE
                    connected_ip = message[1]
                    playing = True
                    waiting_answer = False
                elif message[2] == "reject":
                    send_answer(message[1], 'received_reject')
                    print(message[0] + " rejected your invite")
                    print()
                    waiting_answer = False
                if message[2] == "received_accept":
                    color = chess.BLACK
                    connected_ip = message[1]
                    playing = True
                elif message[2] == 'move' and playing:
                    move = message[3]
                    game.makeMove(move)
            except Exception as e:
                print (str(e))
                break
        conn.close()
    s.close()

def response_udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('',UDP_PORT))
    while True:
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
                        s.sendto(str.encode(RESPONSE_PACKET), (message[1], UDP_PORT))
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
        s.connect((host_ip, TCP_PORT))
        s.send(str.encode(MESSAGE_PACKET))
    except Exception as e:
        print("Error sending the message, try again: " + str(e))
    s.close()

def send_invite(host_name, host_ip):
    MESSAGE_PACKET = ('[%s, %s, invite]' % (NAME, IP))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(30)
        s.connect((host_ip, TCP_PORT))
        s.send(str.encode(MESSAGE_PACKET))
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

def start_game(color, name):
    global connected_ip
    global game
    game = ChessGame(color, IP, connected_ip)
    game.show()
    lan_chess.exec()

def send_move(game):
    while True:
        if game.moveToSend is not None:
            print("sending")
            move = game.moveToSend.uci()
            MESSAGE_PACKET = ('[%s, %s, move, %s]' % (NAME, IP, move))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.settimeout(30)
                s.connect((connected_ip, TCP_PORT))
                s.send(str.encode(MESSAGE_PACKET))
            except Exception as e:
                print("Error connecting, try again: " + str(e))
            s.close()
            game.moveToSend = None

if __name__ == '__main__':
    #response threads always runs on background
    response_tcp_thread = threading.Thread(target=response_tcp)
    response_tcp_thread.start()
    response_udp_thread = threading.Thread(target=response_udp)
    response_udp_thread.start()
    #announce 3 times on startup

    lan_chess = QApplication([]) #create the Qapplication before everything else or crashes

    username = input("Please enter a username: ")
    NAME = username

    #discovery
    for i in range(0,3):
        while announce_lock:
            continue #wait while the first round finishes
        announce()
    #main loop
    while True:
        try:
            if playing:
                start_game(color, username)
            host_index = int(input("Choose player to invite to a game of chess(-1 to see online players, -2 to check invites , -3 to exit): "))
            if host_index == -3:
                print("exiting")
                sys.exit()
            elif host_index == -1:
                print_connected_hosts()
            elif host_index < len(connected_hosts) and host_index >= 0:
                print("Sending invite to: " + connected_hosts[host_index][0])
                waiting_answer = True
                send_invite(connected_hosts[host_index][0], connected_hosts[host_index][1])
                #wait until the answer is received
                while waiting_answer:
                    pass
        except Exception as e:
            print("Please enter an integer: " + str(e))