import socket, time, threading, chess, time
import chess_engine

PORT = 12345
BUFFER_SIZE = 1500

#this is a workaround, but I could not get any other solution working
#opens a socket to google.com, gets the ip address from that connection and closes it without sending anything
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = s.getsockname()[0]
s.close()

SOCKET = None

def connect(username, game_id, i):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(('192.168.1.' + str(i), PORT))
        #send connect packet
        CONNECT_PACKET = ('[%s, %s, connect]' % (username, game_id))
        s.send(str.encode(CONNECT_PACKET))
        #receive ack
        data = s.recv(BUFFER_SIZE)
        response = data.decode()
        response = response[1:len(response)-1] # remove brackets
        response = response.replace(" ", "")
        response = response.split(",")
        if response[1] == "connected":
            print("connected to " + message[0])
            SOCKET = socket
    except:
    	s.close()

def join_game(username, game_id):
    socket = None
    for i in range(0, 256):
        connect_thread = threading.Thread(target=connect, args=[username, game_id, i])

def start_game(color):
    '''
    chessTitan = QApplication([])
    window = MainWindow(chess.WHITE)
    window.show()
    chessTitan.exec()
    '''
    print("starting game")

def sendMove():
    print()

def create_game(username, game_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP,PORT))
    s.listen(1)
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
            global GAME_ID
            if message[2] == 'connect' and message[1] == game_id:
                RESPONSE_PACKET = ('[%s, connected, %s]' % (username, game_id))
                opp_username = message[0]
                conn.send(str.encode(RESPONSE_PACKET))
                #do key exchange then start the game
                start_game(chess.WHITE)
                game_over = False
                while not game_over:
                    #send and receive moves
                    print()
        except Exception as e:
            print (str(e))
            break
    conn.close()
    s.close()

if __name__ == '__main__':
    #response threads always runs on background
    #response_tcp_thread = threading.Thread(target=response_tcp)
    #response_tcp_thread.start()

    #response_udp_thread = threading.Thread(target=response_udp)
    #response_udp_thread.start()
    username = input("Please enter a username: ")
    while True:
        try:
            game_id = input("Create a game(create) or join a game if you have the game id:").lower()
            if game_id == 'create':
                game_id = str(time.process_time_ns())[0:6] #six digits of the timestamp
                print("Your game id: " + game_id)
                create_game(username, game_id)
            else:
                join_game(username, game_id)
                print("Connecting...")
                time.sleep(1)
                if not SOCKET:
                    print("Could not find game")
                else:
                    #play game
                    print()
        except Exception as e:
            print("Please enter a valid game id: " + str(e))
