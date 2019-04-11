"""
simple_board.py

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, \
                       PASS, is_black_white, coord_to_point, where1d, \
                       MAXSIZE, NULLPOINT
import alphabeta

class SimpleGoBoard(object):

    def get_color(self, point):
        return self.board[point]

    def pt(self, row, col):
        return coord_to_point(row, col, self.size)

    def is_legal(self, point, color):
        """
        Check whether it is legal for color to play on point
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            return True
        elif self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
            
        # General case: detect captures, suicide
        opp_color = GoBoardUtil.opponent(color)
        self.board[point] = color
        legal = True
        has_capture = self._detect_captures(point, opp_color)
        if not has_capture and not self._stone_has_liberty(point):
            block = self._block_of(point)
            if not self._has_liberty(block): # suicide
                legal = False
        self.board[point] = EMPTY
        return legal

    def _detect_captures(self, point, opp_color):
        """
        Did move on point capture something?
        """
        for nb in self.neighbors_of_color(point, opp_color):
            if self._detect_capture(nb):
                return True
        return False

    def get_empty_points(self):
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def __init__(self, size):
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)

    def reset(self, size):
        """
        Creates a start state, an empty board with the given size
        The board is stored as a one-dimensional array
        See GoBoardUtil.coord_to_point for explanations of the array encoding
        """
        self.size = size
        self.NS = size + 1
        self.WE = 1
        self.ko_recapture = None
        self.current_player = BLACK
        self.maxpoint = size * size + 3 * (size + 1)
        self.board = np.full(self.maxpoint, BORDER, dtype = np.int32)
        self.liberty_of = np.full(self.maxpoint, NULLPOINT, dtype = np.int32)
        self._initialize_empty_points(self.board)
        self._initialize_neighbors()
        self.index = {
            "horizontal1":(9,10,11,12,13,14,15),
            "horizontal2":(17,18,19,20,21,22,23),
            "horizontal3":(25,26,27,28,29,30,31),
            "horizontal4":(33,34,35,36,37,38,39),
            "horizontal5":(41,42,43,44,45,46,47),
            "horizontal6":(49,50,51,52,53,54,55),
            "horizontal7":(57,58,59,60,61,62,63),

            "vertical1":(9,17,25,33,41,49,57),
            "vertical2":(10,18,26,34,42,50,58),
            "vertical3":(59,51,42,35,27,19,11),
            "vertical4":(12,20,28,36,44,52,60),
            "vertical5":(13,21,29,37,45,53,61),
            "vertical6":(14,22,30,38,46,54,62),
            "vertical7":(15,23,31,35,47,55,63),

            "SWtoNE1":(11,20,29,38,47),
            "SWtoNE2":(10,19,28,37,46,55),
            "SWtoNE3":(9,18,27,36,45,54,63),
            "SWtoNE4":(17,26,35,44,53,62),
            "SWtoNE5":(25,34,43,52,61),

            "SEtoNW1":(13,20,27,34,41),
            "SEtoNW2":(14,21,28,35,42,49),
            "SEtoNW3":(15,22,29,36,43,50,57),
            "SEtoNW4":(23,30,37,44,51,58),
            "SEtoNW5":(31,38,45,52,59)
        }

    def copy(self):
        b = SimpleGoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def row_start(self, row):
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1
        
    def _initialize_empty_points(self, board):
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start = self.row_start(row)
            board[start : start + self.size] = EMPTY

    def _on_board_neighbors(self, point):
        nbs = []
        for nb in self._neighbors(point):
            if self.board[nb] != BORDER:
                nbs.append(nb)
        return nbs
            
    def _initialize_neighbors(self):
        """
        precompute neighbor array.
        For each point on the board, store its list of on-the-board neighbors
        """
        self.neighbors = []
        for point in range(self.maxpoint):
            if self.board[point] == BORDER:
                self.neighbors.append([])
            else:
                self.neighbors.append(self._on_board_neighbors(point))
        
    def is_eye(self, point, color):
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = GoBoardUtil.opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge # 0 at edge, 1 in center
    
    def _is_surrounded(self, point, color):
        """
        check whether empty point is surrounded by stones of color.
        """
        for nb in self.neighbors[point]:
            nb_color = self.board[nb]
            if nb_color != color:
                return False
        return True

    def _stone_has_liberty(self, stone):
        lib = self.find_neighbor_of_color(stone, EMPTY)
        return lib != None

    def _get_liberty(self, block):
        """
        Find any liberty of the given block.
        Returns None in case there is no liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            lib = self.find_neighbor_of_color(stone, EMPTY)
            if lib != None:
                return lib
        return None

    def _has_liberty(self, block):
        """
        Check if the given block has any liberty.
        Also updates the liberty_of array.
        block is a numpy boolean array
        """
        lib = self._get_liberty(block)
        if lib != None:
            assert self.get_color(lib) == EMPTY
            for stone in where1d(block):
                self.liberty_of[stone] = lib
            return True
        return False

    def _block_of(self, stone):
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        marker = np.full(self.maxpoint, False, dtype = bool)
        pointstack = [stone]
        color = self.get_color(stone)
        assert is_black_white(color)
        marker[stone] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _fast_liberty_check(self, nb_point):
        lib = self.liberty_of[nb_point]
        if lib != NULLPOINT and self.get_color(lib) == EMPTY:
            return True # quick exit, block has a liberty  
        if self._stone_has_liberty(nb_point):
            return True # quick exit, no need to look at whole block
        return False
        
    def _detect_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        Returns boolean.
        """
        if self._fast_liberty_check(nb_point):
            return False
        opp_block = self._block_of(nb_point)
        return not self._has_liberty(opp_block)
    
    def _detect_and_process_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
            and returns None otherwise.
        This result is used in play_move to check for possible ko
        """
        if self._fast_liberty_check(nb_point):
            return None
        opp_block = self._block_of(nb_point)
        if self._has_liberty(opp_block):
            return None
        captures = list(where1d(opp_block))
        self.board[captures] = EMPTY
        self.liberty_of[captures] = NULLPOINT
        single_capture = None 
        if len(captures) == 1:
            single_capture = nb_point
        return single_capture

    def play_move(self, point, color):
        """
        Play a move of color on point
        Returns boolean: whether move was legal
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            self.ko_recapture = None
            self.current_player = GoBoardUtil.opponent(color)
            return True
        elif self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
            
        # General case: deal with captures, suicide, and next ko point
        opp_color = GoBoardUtil.opponent(color)
        in_enemy_eye = self._is_surrounded(point, opp_color)
        self.board[point] = color
        single_captures = []
        neighbors = self.neighbors[point]
        for nb in neighbors:
            if self.board[nb] == opp_color:
                single_capture = self._detect_and_process_capture(nb)
                if single_capture != None:
                    single_captures.append(single_capture)
        if not self._stone_has_liberty(point):
            # check suicide of whole block
            block = self._block_of(point)
            if not self._has_liberty(block): # undo suicide move
                self.board[point] = EMPTY
                return False
        self.ko_recapture = None
        if in_enemy_eye and len(single_captures) == 1:
            self.ko_recapture = single_captures[0]
        self.current_player = GoBoardUtil.opponent(color)
        return True

    def neighbors_of_color(self, point, color):
        """ List of neighbors of point of given color """
        nbc = []
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc
        
    def find_neighbor_of_color(self, point, color):
        """ Return one neighbor of point of given color, or None """
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                return nb
        return None
        
    def _neighbors(self, point):
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point):
        """ List of all four diagonal neighbors of point """
        return [point - self.NS - 1, 
                point - self.NS + 1, 
                point + self.NS - 1, 
                point + self.NS + 1]
    
    def _point_to_coord(self, point):
        """
        Transform point index to row, col.
        
        Arguments
        ---------
        point
        
        Returns
        -------
        x , y : int
        coordination of the board  1<= x <=size, 1<= y <=size .
        """
        if point is None:
            return 'pass'
        row, col = divmod(point, self.NS)
        return row, col

    def is_legal_gomoku(self, point, color):
        """
            Check whether it is legal for color to play on point, for the game of gomoku
            """
        return self.board[point] == EMPTY
    
    def play_move_gomoku(self, point, color):
        """
            Play a move of color on point, for the game of gomoku
            Returns boolean: whether move was legal
            """
        assert is_black_white(color)
        assert point != PASS
        if self.board[point] != EMPTY:
            return False
        self.board[point] = color
        self.current_player = GoBoardUtil.opponent(color)
        return True
        
    def _point_direction_check_connect_gomoko(self, point, shift):
        """
        Check if the point has connect5 condition in a direction
        for the game of Gomoko.
        """
        color = self.board[point]
        count = 1
        d = shift
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == 5:
                    break
            else:
                break
        d = -d
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == 5:
                    break
            else:
                break
        assert count <= 5
        return count == 5
    
    def point_check_game_end_gomoku(self, point):
        """
            Check if the point causes the game end for the game of Gomoko.
            """
        # check horizontal
        if self._point_direction_check_connect_gomoko(point, 1):
            return True
        
        # check vertical
        if self._point_direction_check_connect_gomoko(point, self.NS):
            return True
        
        # check y=x
        if self._point_direction_check_connect_gomoko(point, self.NS + 1):
            return True
        
        # check y=-x
        if self._point_direction_check_connect_gomoko(point, self.NS - 1):
            return True
        
        return False
    
    def check_game_end_gomoku(self):
        """
            Check if the game ends for the game of Gomoku.
            """
        white_points = where1d(self.board == WHITE)
        black_points = where1d(self.board == BLACK)
        
        for point in white_points:
            if self.point_check_game_end_gomoku(point):
                return True, WHITE
    
        for point in black_points:
            if self.point_check_game_end_gomoku(point):
                return True, BLACK

        return False, None

    def solve(self):
        result, move, drawMove = alphabeta.solve(self)
        if move=="First":
            if result==0:
                return 'draw',drawMove
            else:
                winner='w' if self.current_player!=WHITE else 'b'
                return winner,'NoMove'
        elif move=="NoMove":
            if result:
                return 'draw', drawMove
            else:
                winner='w' if self.current_player!=WHITE else 'b'
                return winner, move
        else:
            winner='w' if self.current_player==WHITE else 'b'
            return winner, move

    def check_pattern(self,point,have,direction_x,direction_y,moveSet,patternList,color,flag):
        for i in range(0,4):
            if have in patternList[i]:
                for dis in patternList[i][have]:
                    moveSet[i].add(point-direction_x*(dis+1)-direction_y*self.NS*(dis+1))
                #flag[0]=True
                break
        if (not (0<= point<len(self.board))) or len(have)==9:
            return
#if self.get_color(point)==BORDER or len(have)==7:
#            return
        piece=self.get_color(point)
        if piece==EMPTY:
            piece='.'
        elif piece==color:
            piece='x'
        elif piece == BORDER:
            piece='B'
        else:
            piece='o'
        have+=piece
        #print(GoBoardUtil.format_point(self._point_to_coord(point)),have,self.board[point])
        self.check_pattern(point+direction_x+direction_y*self.NS,have,direction_x,direction_y,moveSet,patternList,color,flag)

    def get_pattern_moves(self):
        """
        1. direct winning point xxxx. x.xxx xx.xx
        2. urgent blocking point xoooo.
        3. wining in 2 step point
        """
        moveSet=[set(),set(),set(),set()]
        color=self.current_player

        patternList=[{'xxxx.':{0},'xxx.x':{1},'xx.xx':{2},'x.xxx':{3},'.xxxx':{4}}, #win
                     {'oooo.':{0},'ooo.o':{1},'oo.oo':{2},'o.ooo':{3},'.oooo':{4}}, #block win
                     {'.xxx..':{1},'..xxx.':{4},'.xx.x.':{2},'.x.xx.':{3}}, #make-four
                     {'.ooo..':{1,5},'..ooo.':{0,4},'.oo.o.':{0,2,5},'.o.oo.':{0,3,5}, 'B.ooo..':{0}, '..ooo.B':{6},
                     'x.ooo..':{0}, '..ooo.x':{6} #block-open-four
                     }]

        direction_x=[1,0,1,-1]
        direction_y=[0,1,1,1]
        flag=[False]

        for point in range(0, len(self.board)):
            if flag[0]:
                break
            for direction in range(0,4):
                    self.check_pattern(point,'',direction_x[direction],direction_y[direction],moveSet,patternList,color,flag)
        
        i=0
        while i<4 and not bool(moveSet[i]): i+=1
        if i==4:
            return i,None
        else:
            return i, list(moveSet[i])
            
    def list_solve_point(self):
        """
        1. direct winning point xxxx. x.xxx xx.xx
        2. urgent blocking point xoooo.
        3. wining in 2 step point
        """
        moveSet=[set(),set(),set(),set()]
        color=self.current_player

        patternList=[{'xxxx.':{0},'xxx.x':{1},'xx.xx':{2},'x.xxx':{3},'.xxxx':{4}},{'oooo.':{0},'ooo.o':{1},'oo.oo':{2},'o.ooo':{3},'.oooo':{4}},{'.xxx..':{1},'..xxx.':{4},'.xx.x.':{2},'.x.xx.':{3}},{'.ooo..':{1,5},'..ooo.':{0,4},'.oo.o.':{2},'.o.oo.':{3}}]

        direction_x=[1,0,1,-1]
        direction_y=[0,1,1,1]
        flag=[False]

        for point in where1d(self.board!=BORDER):
            if flag[0]:
                break
            for direction in range(0,4):
                    self.check_pattern(point,'',direction_x[direction],direction_y[direction],moveSet,patternList,color,flag)
        
        i=0
        while i<4 and not bool(moveSet[i]):
            i+=1
        if i==4:
            return None
        else:
            return list(moveSet[i])

    def get_expension_score(self):
        score = 0
        for key in self.index.key():
            pattern = ""
            for index in self.check_pattern:
                pattern += self.board[index]
            score += self.check_pattern(pattern)

        return score

    def check_pattern(self,pattern):
        win = False
        lose = False
        block = False
        
        me = self.current_player
        he = GoBoardUtil.opponent(me)

        l = len(pattern)

        if l == 7:
            if pattern[2] == he:
                if (pattern[3]==me |pattern[4] == me):
                    block = True
                else:
                    lose = True

            elif pattern[3] == he:
                if (pattern[1]==me | pattern[2] == me | pattern[4]==me |pattern[5] == me):
                    block = True
                else:
                    lose = True

            elif pattern[4] == he:
                if (pattern[2]==me | pattern[3] == me):
                    block = True
                else:
                    lose = True

            elif pattern[2] == me:
                if (pattern[3]==he |pattern[4] == he):
                    block = True
                else:
                    win = True
            
            elif pattern[3] == me:
                if (pattern[1]==he | pattern[2] == he | pattern[4]==he |pattern[5] == he):
                    block = True
                else:
                    win = True
            
            elif pattern[4] == me:
                if (pattern[2]==he | pattern[3] == he):
                    block = True
                else:
                    win = True
        elif l ==6 :
            if pattern[1] == he:
                if (pattern[2]==me | pattern[3] == me | pattern[4]==me):
                    block = True
                else:
                    lose = True
            elif pattern[2] == he:
                if (pattern[3]==me | pattern[4] == me| pattern[1]==me):
                    block = True
                else:
                    lose = True 
            elif pattern[4] == he:
                if (pattern[1]==me | pattern[2] == me| pattern[3]==me):
                    block = True
                else:
                    lose = True 
            elif pattern[1] == me:
                if (pattern[2]==he | pattern[3] == he | pattern[4]==he):
                    block = True
                else:
                    win = True
            elif pattern[2] == me:
                if (pattern[3]==he | pattern[4] == he | pattern[1]==he):
                    block = True
                else:
                    win = True
            elif pattern[4] == me:
                if (pattern[1]==he | pattern[2] == he | pattern[3]==he):
                    block = True
                else:
                    win = True

        elif l == 5:
            if me in pattern:
                if he not in pattern:
                    win = True
                else:
                    block = True
            if he in pattern:
                lose = True
        
        if block:
            return 0
        elif win:
            return 10
        elif lose:
            return -10
    
    def expansion(self):
        empty_points = self.get_empty_points
        if len(empty_points) == 49:
            return 36
        if len(empty_points) == 48 and self.get_color(36) == EMPTY:
            return 36

        best = -1000
        best_move = None
        for point in empty_points:
            self.board[point] = self.current_player
            score = self.get_expension_score
            if score > best:
                best = score
                best_move = point
            self.board[point] = EMPTY
            

