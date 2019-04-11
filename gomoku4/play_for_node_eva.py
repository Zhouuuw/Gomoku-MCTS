"""
helper class for playGame in MCTS.py file
"""


from board_util import GoBoardUtil, BLACK, WHITE, PASS, EMPTY
from simple_board import SimpleGoBoard
import random


def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def play_move(board, move, color):
    board.play_move_gomoku(move, color)

def game_result(board):
    game_end, winner = board.check_game_end_gomoku()
    moves = board.get_empty_points()
    board_full = (len(moves) == 0)
    if game_end:
        #return 1 if winner == board.current_player else -1
        return winner
    if board_full:
        return 'draw'
    return None

def policy_moves(board, color_to_play):
       # if(self.playout_policy=='random'):
        #    return "Random", self._random_moves(board, color_to_play)
        #else:
         #   assert(self.playout_policy=='rule_based')
          #  assert(isinstance(board, SimpleGoBoard))
        pattern_list=['Win', 'BlockWin', 'OpenFour', 'BlockOpenFour', 'Random']
        ret=board.get_pattern_moves()
        if ret is None:
            return "Random", GoBoardUtil.generate_legal_moves_gomoku(board)
    
        movetype_id, moves=ret
        return pattern_list[movetype_id], moves
    


class Play_for_evaluate(object):
    
    
    """
    it seems get pass point after some simulation, how to run as much as simulation as possible in time limit
    try cumulative winning result in each simulate game 
    """

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)


    @staticmethod
    def playGame(board, toPlay):
        """
        run simulation game 
        """
        limit = 1000
        simulation_moves=[]
        #cboard = board.copy()
        nuPasses = 0
        for _ in range(limit):
        #while True:
            color = board.current_player
            playout_move = GoBoardUtil.generate_random_move_gomoku(board)
            if playout_move != None:
                if_legal = board.play_move_gomoku(playout_move, color)
                #simulation_moves.append(playout_move)
                #_, res = board.check_game_end_gomoku()
                #print(if_legal)
                if not if_legal:
                    print("illegal move#")
                #assert if_legal
            else:
                #board.play_move_gomoku(playout_move, color)
                if playout_move == PASS:
                    break
                    #nuPasses +=1
                #else nuPasses = 0
                #if nuPasses >= 2:
                 #   break
            color = GoBoardUtil.opponent(color)
        _, winner = board.check_game_end_gomoku()
        return winner

    @staticmethod
    def do_playout(board, color_to_play):
        res=game_result(board)
        simulation_moves=[]
        while(res is None):
            _ , candidate_moves = policy_moves(board, board.current_player)
            playout_move=random.choice(candidate_moves)
            play_move(board, playout_move, board.current_player)
            simulation_moves.append(playout_move)
            res=game_result(board)
        for m in simulation_moves[::-1]:
            undo(board, m)
        if res == color_to_play:
            return 1.0
        elif res == 'draw':
            return 0.0
        else:
            assert(res == GoBoardUtil.opponent(color_to_play))
            return -1.0

    