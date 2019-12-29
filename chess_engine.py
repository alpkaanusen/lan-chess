import chess
import socket
import chess.svg
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox

class ChessGame(QWidget):
    def __init__(self, color, ip, connected_ip):
        super().__init__()

        self.setWindowTitle("LAN Chess")
        self.setGeometry(300, 300, 800, 800)

        self.widgetSvg = QSvgWidget(parent=self)
        self.svgX = 50                          # top left x-pos of chessboard
        self.svgY = 50                          # top left y-pos of chessboard
        self.cbSize = 600                       # size of chessboard
        self.widgetSvg.setGeometry(self.svgX,self.svgY, self.cbSize, self.cbSize)
        self.coordinates = True
        self.color = color #True for white, False for black
        self.margin = 0.05*self.cbSize if self.coordinates == True else 0
        self.squareSize  = (self.cbSize - 2 * self.margin) / 8.0
        self.chessboard = chess.Board()
        self.squareToMove = None
        self.selectedPiece = None
        self.squares = None
        self.lastMove = None
        self.check = None
        self.connected_ip = connected_ip
        self.ip = ip
        self.port = 12345
    
    @pyqtSlot(QWidget)
    def mousePressEvent(self, event):
        if self.chessboard.turn != self.color: # not this players turn
            return
        if self.svgX < event.x() <= self.svgX + self.cbSize and self.svgY < event.y() <= self.svgY + self.cbSize:   # mouse on chessboard
            if event.buttons() == Qt.LeftButton:
                # if the click is on chessBoard only
                if self.svgX + self.margin < event.x() < self.svgX + self.cbSize - self.margin and self.svgY + self.margin < event.y() < self.svgY + self.cbSize - self.margin:
                    #get file and rank of the selected square
                    file = int((event.x() - (self.svgX + self.margin))/self.squareSize)             
                    rank = 7 - int((event.y() - (self.svgY + self.margin))/self.squareSize) 
                    if not self.color: # black
                        file = 7 - file 
                        rank = 7 - rank

                    #to check if a piece is on the square
                    square = chess.square(file, rank)
                    piece = self.chessboard.piece_at(square)
                    
                    selected_square = '{}{}'.format(chess.FILE_NAMES[file], chess.RANK_NAMES[rank]) # selected squares coordinates as a string 
    
                    if self.selectedPiece is not None and self.squareToMove != selected_square:
                        move = chess.Move.from_uci('{}{}'.format(self.squareToMove, selected_square))
                        if move in self.chessboard.legal_moves:
                            self.chessboard.push(move)
                            self.lastMove = move
                            #to-do: send the move to the opponent
                            move = move.uci()
                            MESSAGE_PACKET = ('[%s, %s, move, %s]' % ('NAME', self.ip, move))
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            try:
                                s.settimeout(5)
                                s.connect((self.connected_ip, self.port))
                                s.send(str.encode(MESSAGE_PACKET))
                            except Exception as e:
                                print("Error connecting, try again: " + str(e))
                            s.close()
                            if self.chessboard.is_check():
                                self.check = self.chessboard.king(self.chessboard.turn) # finds the checked king
                            else:
                                self.check = None
                            if self.chessboard.is_game_over():
                                self.showGameOverMessage("Result: " + str(self.chessboard.result()))
                        self.squareToMove = None
                        self.selectedPiece = None
                        self.squares = None 
                    else:
                        if piece is not None:# and self.color and piece.color: # check if the selected piece is this player's piece
                            self.squareToMove = selected_square
                            self.selectedPiece = piece 
                            self.squares = chess.SquareSet()   
                            for legal_move in self.chessboard.legal_moves:
                                if legal_move.from_square == square: #show legal moves from the selected square
                                    self.squares.add(legal_move.to_square)
                        else:
                            self.squareToMove = None
                            self.selectedPiece = None  
                            self.squares = None                                 
                # update the board
                self.update()
        else:
            QWidget.mousePressEvent(self, event)

    @pyqtSlot(QWidget)
    def paintEvent(self, event):
        self.chessboardSvg = chess.svg.board(self.chessboard, size = self.cbSize, coordinates = self.coordinates, check = self.check, lastmove = self.lastMove, flipped = not self.color, squares = self.squares).encode("UTF-8")
        self.widgetSvg.load(self.chessboardSvg)
    
    #for opponent's moves
    def makeMove(self, move):
        move = chess.Move.from_uci(move)
        if move in self.chessboard.legal_moves:
            self.chessboard.push(move)
            self.lastMove = move
            #to-do: send the move to the opponent
            if self.chessboard.is_check():
                self.check = self.chessboard.king(self.chessboard.turn) # finds the checked king
            else:
                self.check = None
            if self.chessboard.is_game_over():
                showGameOverMessage("Result: " + str(self.chessboard.result()))
    
    def showGameOverMessage(self, message):
        QMessageBox.about(self, "Game Over", message)
        #message = QMessageBox.question(self, 'PyQt5 message', "Do you like PyQt5?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        self.close()
