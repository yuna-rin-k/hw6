#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import logging
import random
import webapp2
import time

# Reads json description of the board and provides simple interface.
class Game:
    # Takes json or a board directly.
    def __init__(self, body=None, board=None):
                if body:
                        game = json.loads(body)
                        self._board = game["board"]
                else:
                        self._board = board

    # Returns piece on the board.
    # 0 for no pieces, 1 for player 1, 2 for player 2.
    # None for coordinate out of scope.
    def Pos(self, x, y):
        return Pos(self._board["Pieces"], x, y)

    # Returns who plays next.
    def Next(self):
        return self._board["Next"]

    # Returns the array of valid moves for next player.
    # Each move is a dict
    #   "Where": [x,y]
    #   "As": player number
    def ValidMoves(self):
                moves = []
                for y in xrange(1,9):
                        for x in xrange(1,9):
                                move = {"Where": [x,y],
                                        "As": self.Next()}
                                if self.NextBoardPosition(move):
                                        moves.append(move)
                return moves

    # Helper function of NextBoardPosition.  It looks towards
    # (delta_x, delta_y) direction for one of our own pieces and
    # flips pieces in between if the move is valid. Returns True
    # if pieces are captured in this direction, False otherwise.
    def __UpdateBoardDirection(self, new_board, x, y, delta_x, delta_y):
        player = self.Next()
        opponent = 3 - player
        look_x = x + delta_x
        look_y = y + delta_y
        flip_list = []
        while Pos(new_board, look_x, look_y) == opponent:
            flip_list.append([look_x, look_y])
            look_x += delta_x
            look_y += delta_y
        if Pos(new_board, look_x, look_y) == player and len(flip_list) > 0:
                        # there's a continuous line of our opponents
                        # pieces between our own pieces at
                        # [look_x,look_y] and the newly placed one at
                        # [x,y], making it a legal move.
            SetPos(new_board, x, y, player)
            for flip_move in flip_list:
                flip_x = flip_move[0]
                flip_y = flip_move[1]
                SetPos(new_board, flip_x, flip_y, player)
            return True
        return False

    # Takes a move dict and return the new Game state after that move.
    # Returns None if the move itself is invalid.
    def NextBoardPosition(self, move):
        x = move["Where"][0]
        y = move["Where"][1]
        if self.Pos(x, y) != 0:
                        # x,y is already occupied.
                        return None
        new_board = copy.deepcopy(self._board)
        pieces = new_board["Pieces"]

        if not (self.__UpdateBoardDirection(pieces, x, y, 1, 0)
                        | self.__UpdateBoardDirection(pieces, x, y, 0, 1)
                | self.__UpdateBoardDirection(pieces, x, y, -1, 0)
                | self.__UpdateBoardDirection(pieces, x, y, 0, -1)
                | self.__UpdateBoardDirection(pieces, x, y, 1, 1)
                | self.__UpdateBoardDirection(pieces, x, y, -1, 1)
                | self.__UpdateBoardDirection(pieces, x, y, 1, -1)
                | self.__UpdateBoardDirection(pieces, x, y, -1, -1)):
                        # Nothing was captured. Move is invalid.
                return None
                
                # Something was captured. Move is valid.
        new_board["Next"] = 3 - self.Next()
        return Game(board=new_board)

# Returns piece on the board.
# 0 for no pieces, 1 for player 1, 2 for player 2.
# None for coordinate out of scope.
#
# Pos and SetPos takes care of converting coordinate from 1-indexed to
# 0-indexed that is actually used in the underlying arrays.
def Pos(board, x, y):
    if 1 <= x and x <= 8 and 1 <= y and y <= 8:
        return board[y-1][x-1]
    return None

# Set piece on the board at (x,y) coordinate
def SetPos(board, x, y, piece):
    if x < 1 or 8 < x or y < 1 or 8 < y or piece not in [0,1,2]:
        return False
    board[y-1][x-1] = piece

# Debug function to pretty print the array representation of board.
def PrettyPrint(board, nl="<br>"):
    s = ""
    for row in board:
        for piece in row:
            s += str(piece)
        s += nl
    return s

def PrettyMove(move):
    m = move["Where"]
    return '%s%d' % (chr(ord('A') + m[0] - 1), m[1])

class MainHandler(webapp2.RequestHandler):
    # Handling GET request, just for debugging purposes.
    # If you open this handler directly, it will show you the
    # HTML form here and let you copy-paste some game's JSON
    # here for testing.
    def get(self):
        if not self.request.get('json'):
          self.response.write("""
<body><form method=get>
Paste JSON here:<p/><textarea name=json cols=80 rows=24></textarea>
<p/><input type=submit>
</form>
</body>
""")
          return
        else:
          g = Game(self.request.get('json'))
          self.pickMove(g)

    def post(self):
        # Reads JSON representation of the board and store as the object.
        g = Game(self.request.body)
        # Do the picking of a move and print the result.
        self.pickMove(g)


    def pickMove(self, g):
        # Gets all valid moves.
        valid_moves = g.ValidMoves()
        if len(valid_moves) == 0:
            # Passes if no valid moves.
            self.response.write("PASS")
        else:
            # Chooses a valid move randomly if available.
                # TO STEP STUDENTS:
                # You'll probably want to change how this works, to do something
                # more clever than just picking a random move.

            #move = random.choice(valid_moves)
            countOfPiece = 0
            for i in xrange(1,9):
                for j in xrange(1,9):
                    if g.Pos(i, j) != 0:
                        countOfPiece = countOfPiece + 1
            begin = time.time()
            move = MainHandler.runMaxmin(self, g, countOfPiece, g.Next(), begin)
            self.response.write(PrettyMove(move))


    def runMaxmin(self, g, countOfPiece, player, begin):

        bestMove = {"Where":[0,0]}
        bestScore0 = -10000000
        score = 0

        for move in g.ValidMoves():

            x = move["Where"][0]
            y = move["Where"][1]


            if MainHandler.isAngle(self, x, y):
                return move

            if MainHandler.changeScores0(self, g, x, y, player):
                return move

            gameBoard = g.NextBoardPosition(move)
            
            score = MainHandler.maxmin(self, 2, gameBoard, countOfPiece, player, begin, player, gameBoard)

            if score > bestScore0:
                bestScore0 = score
                bestMove = move

        return bestMove

    def maxmin(self, depth, g, countOfPiece, player, begin, PLAYER, GAMEBOARD):
        move = {"Where":[0,0]}

        return MainHandler.alphabeta(self, depth, g, -9999999, 9999999, countOfPiece, False, player, move, begin, PLAYER)


    #return score
    def alphabeta(self, depth, g, alpha, beta, countOfPiece, isMe, player, move, begin, PLAYER):

        end = time.time()

        if depth == 0 or end - begin >= 13:
            
            if countOfPiece <= 60:
                return MainHandler.middleCalcScore(self, g, PLAYER, countOfPiece)
            return MainHandler.finalStageScore(self, g, PLAYER)
        
        if isMe:
            moves = g.ValidMoves()
            for move in moves:
                gameBoard = g.NextBoardPosition(move)
                alpha0 = MainHandler.alphabeta(self, depth-1, gameBoard, alpha, beta, countOfPiece, False, player, move, begin, PLAYER)
                alpha = max(alpha, alpha0)
                if alpha >= beta:
                    break
            return alpha

        else:
            moves = g.ValidMoves()
            for move in moves:
                gameBoard = g.NextBoardPosition(move)
                beta0 = MainHandler.alphabeta(self, depth-1, gameBoard, alpha, beta, countOfPiece, True, player, move, begin, PLAYER)
                beta = min(beta, beta0)
                if alpha >= beta:
                    break
            return beta
    

    def middleCalcScore(self, g, player, countOfPiece):

        black = 0
        white = 0

        scores = [9000,-3000,130,130,130,130,-3000,9000],[-3000, -5000, 0, 0, 0, 0, -5000, -3000],[130, 0, 45, 35, 35, 45, 0, 130],[130, 0, 45, 45, 45, 45, 0, 130],[130, 0, 45, 45, 45, 45, 0, 130],[130, 0, 45, 35, 35, 45, 0, 130],[-3000, -5000, 0, 0, 0, 0, -5000, -3000],[9000, -3000, 130, 130, 130, 130, -3000, 9000]

        for i in xrange(1, 9):
            for j in xrange(1, 9):

                if g.Pos(j, i) == 1:

                    if MainHandler.changeScores0_1(self, g, i, j, 1):
                        black += 130
                    elif MainHandler.changeScores0(self, g, i ,j, 1):
                        black += 200
                    elif MainHandler.changeScores0(self, g, i, j, 2):
                        black += 0
                    else:
                        black +=scores[i-1][j-1]


                elif g.Pos(j, i) == 2:

                    if MainHandler.changeScores0_1(self, g, i, j, 2):
                        white += 130
                    elif MainHandler.changeScores0(self, g, i, j, 2):
                        white += 200
                    elif MainHandler.changeScores0(self, g, i, j, 1):
                        white += 0
                    else:
                        white += scores[i-1][j-1]


        nextPlayer = g.Next()
        if player == 1:
            if nextPlayer == 1 and MainHandler.hasTwoAngle(self, g) == False:
                return black - white + len(g.ValidMoves()) * 300
            elif nextPlayer == 2 and MainHandler.hasTwoAngle(self, g) == False:
                return black - white - len(g.ValidMoves()) * 300
            return black - white

        else:
            if nextPlayer == 2 and MainHandler.hasTwoAngle(self, g) == False:
                return white - black + len(g.ValidMoves()) * 300
            elif nextPlayer == 1 and MainHandler.hasTwoAngle(self, g) == False:
                return white - black - len(g.ValidMoves()) * 300
            return white - black


    def finalStageScore(self, g, player):

        black = 0
        white = 0

        for i in xrange(1, 9):
            for j in xrange(1, 9):

                if g.Pos(j, i) == 1:
                    black += 50
                elif g.Pos(j, i) == 2:
                    white += 50

        if player == 1:
            return black - white

        return white - black

    def isAngle(self, x, y):

        if x == 1 and y == 1:
            return True
        if x == 1 and y == 8:
            return True
        if x == 8 and y == 1:
            return True
        if x == 8 and y == 8:
            return True

        return False

    def hasTwoAngle(self, g):

        numOfAngle = 0

        if g.Pos(1, 1) != 0:
            numOfAngle += 1
        if g.Pos(1, 8) != 0:
            numOfAngle += 1
        if g.Pos(8, 1) != 0:
            numOfAngle += 1
        if g.Pos(8, 8) != 0:
            numOfAngle += 1

        if numOfAngle >= 2:
            return True
        return False

    def changeScores0(self, g, x, y, player):

        if g.Pos(1, 1) == player:
            if (x == 1 and y == 2) or (x == 2 and y == 1) or (x == 2 and y == 2):
                return True
               
        if g.Pos(1, 8) == player:
            if (x == 1 and y == 7) or (x == 2 and y == 7) or (x == 2 and y == 8):
                return True

        if g.Pos(8, 1) == player:
            if (x == 7 and y == 1) or (x == 7 and y == 2) or (x == 8 and y == 2):
                return True

        if g.Pos(8, 8) == player:
            if (x == 7 and y == 8) or (x == 8 and y == 7) or (x == 7 and y == 7):
                return True
       
        return False

    def changeScores0_1(self, g, x, y, player):

        if g.Pos(1, 1) == player:
            if x == 2 and y == 2:
                return True
               
        if g.Pos(1, 8) == player:
            if x == 2 and y == 7:
                return True

        if g.Pos(8, 1) == player:
            if x == 7 and y == 2:
                return True

        if g.Pos(8, 8) == player:
            if x == 7 and y == 7:
                return True
       
        return False

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
