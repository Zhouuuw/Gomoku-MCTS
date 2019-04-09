"""
mcts class
"""
import time
import math
import random
import copy

from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, \
                       PASS, is_black_white, coord_to_point, where1d, \
                       MAXSIZE, NULLPOINT

"""
class Player(object):
    def __init__(self, board):
        self.board = board

    def set_id(self, id):
        self.id = id

    @property
    def legal_action_list(self):
        return self.board.legal_list


class Node(object):
    def __init__(self, state):
        self.state = copy.copy(state)
        self.win_i = 0   #winnig number at that node
        self.n_i = 0     #total sim number at that node

    def __lt__(self, other):
        return True

    @property
    def x_i(self):
        return self.win_i / self.n_i

    def ucb(self, n):
        return (self.win_i / self.n_i) + math.sqrt(2 * math.log(n) / self.n_i)

class Record(object):
    def __init__(self):
        self.n = 0
        self.nodes = {}

    def find(self, node):      #how is node.state pass to here?; or here node is a instance of class, state is attribute of it
        try:
            return self.nodes[str(node.state)]
        except:
            return None

    def add(self, node):
        self.nodes[str(node.state)] = node

    def clear(self):
        self.nodes = {}




class AI(Player):
    def __init__(self, one_d_board):
        Player.__init__(self, one_d_board)
        self.record = Record()
        self.board = one_d_board

    def act(self):
        action = self.mcts()
        return action

    def mcts(self):
        # find the postion of current state(and) play in the tree,
        # result is logically guaranteed to be found
        self.record.clear()
        current_root = Node(self.board)
        self.record.add(current_root)
        current_root = self.record.find(current_root)

        board = self.board
        #board.set_with_state(current_root.state)
        #legal_action_list = board.legal_list
        legal_action_list = where1d(board == EMPTY)

        print("here is current_root.state " + str(current_root.state))
        #print("here is board.state " + str(board.state))
        
        possible_children = []
        for action in legal_action_list:
            #board.set_with_state(current_root.state)
            player_id = self.check_player(board)
            board.update(player_id, action)
            child = Node(board.state)
            possible_children.append(child)

        for child in possible_children:
            self.record.add(child)
            child_inside = self.record.find(child)
            tmp_board = Board()
            tmp_board.set_with_state(child_inside.state)
            favourable = self.simulate(tmp_board)
            if favourable:                        #if favourable ==1, win
                child_inside.win_i += 1
            child_inside.n_i += 1
            self.record.n += 1

        children = [self.record.find(node) for node in possible_children]
        #print("print children " + str(children))
        

        self.simulation_count = 0
        start_time = time.time()
        #while time.time() - start_time < think_time:
        while True:
            one, _ = self.select(current_root)
            self.simulation_count += 1
            tmp_board = Board()
            tmp_board.set_with_state(one.state)
            favourable = self.simulate(tmp_board)
            if favourable:
                one.win_i += 1
            one.n_i += 1
            self.record.n += 1

        value, node = max(
            [node.x_i, node] for node in children
        )


        diff = (np.array(current_root.state) - np.array(node.state)).tolist()
        #print('this is diff ' + str(diff))
        action = diff.index(min(diff))

        print("simulation_count:", self.simulation_count)
        return action

    def select(self, current_node):
        board = Board()
        board.set_with_state(current_node.state)
        legal_action_list = board.legal_list

        possible_children = []
        for action in legal_action_list:
            board.set_with_state(current_node.state)
            player_id = self.check_player(board.state)
            board.update(player_id, action)
            child = Node(board.state)
            possible_children.append(child)

        children = [self.record.find(node) for node in possible_children]
        if(all(children)):
            value, node = max([
                [node.ucb(self.record.n), node] for node in children
            ])
            return node, False
        else:
            return None, True

    def simulate(self, board):
        # self.graphic(board)
        copy_board = copy.deepcopy(board)
        current_player = self.check_player(copy_board.state)

        # rand process
        over, winner = copy_board.check_game_process()
        player_id = current_player
        while not over:
            action = random.choice(copy_board.legal_list)
            copy_board.update(player_id, action)
            over, winner = copy_board.check_game_process()
            player_id = self.check_player(copy_board.state)
        # rand process

        #print(board.state)
        

        return winner != current_player

    def check_player(self, state):
        player1_count = state.count(1)
        player2_count = state.count(2)
        # 1 first, so if equal, return 1
        return 2 if player1_count > player2_count else 1

    def rand_act(self):
        legal_action_list = self.legal_action_list

        return random.choice(legal_action_list)


    def __str__(self):
        return "AI"

"""

class MCTS(object):
    """
    AI player, use Monte Carlo Tree Search with UCB
    """

    def __init__(self, board, play_turn, max_actions=1000):
        self.board = board
        self.play_turn = play_turn
        self.calculation_time = float(3)
        self.max_actions = max_actions
        self.n_in_row = 5

        self.player = play_turn[0] # AI is first at now
        self.confident = 1.96
        self.max_depth = 1

    def get_action(self):
        availables = self.board.get_empty_points()
        print("availables " + str(availables))
        #if len(availables) == 1:
         #   return availables[0]

        self.plays = {} # key:(player, move), value:visited times
        self.wins = {} # key:(player, move), value:win times
        simulations = 0
        begin = time.time()
        while time.time() - begin < self.calculation_time:
            board_copy = copy.deepcopy(self.board)  # simulation will change board's states,
            play_turn_copy = copy.deepcopy(self.play_turn) # and play turn
            self.run_simulation(board_copy, play_turn_copy)
            simulations += 1

        print("total simulations=", simulations)

        move = self.select_one_move()
        #location = self.board.move_to_location(move)
        print('Maximum depth searched:', self.max_depth)

        #print("AI move: %d,%d\n" % (location[0], location[1]))

        return move

    def run_simulation(self, board, play_turn):
        """
        MCTS main process
        """

        plays = self.plays
        wins = self.wins
        availables = board.get_empty_points

        player = self.get_player(play_turn)
        visited_states = set()
        winner = -1
        expand = True
        # Simulation
        for t in range(1, self.max_actions + 1):
            # Selection
            # if all moves have statistics info, choose one that have max UCB value
            if all(plays.get((player, move)) for move in availables):
                log_total = log(
                    sum(plays[(player, move)] for move in availables))
                value, move = max(
                    ((wins[(player, move)] / plays[(player, move)]) +
                     sqrt(self.confident * log_total / plays[(player, move)]), move)
                    for move in availables)   # UCB
            else:
                # a simple strategy
                # prefer to choose the nearer moves without statistics,
                # and then the farthers.
                # try ro add statistics info to all moves quickly
                adjacents = []
                if len(availables) > self.n_in_row:
                    adjacents = self.adjacent_moves(board, player, plays)

                if len(adjacents):
                    move = choice(adjacents)
                else:
                    peripherals = []
                    for move in availables:
                        if not plays.get((player, move)):
                            peripherals.append(move)
                    move = choice(peripherals)

            board.update(player, move)

            # Expand
            # add only one new child node each time
            if expand and (player, move) not in plays:
                expand = False
                plays[(player, move)] = 0
                wins[(player, move)] = 0
                if t > self.max_depth:
                    self.max_depth = t

            visited_states.add((player, move))

            is_full = not len(availables)
            win, winner = self.has_a_winner(board)
            if is_full or win:
                break

            player = self.get_player(play_turn)

        # Back-propagation
        for player, move in visited_states:
            if (player, move) not in plays:
                continue
            plays[(player, move)] += 1 # all visited moves
            if player == winner:
                wins[(player, move)] += 1 # only winner's moves

    def get_player(self, players):
        p = players.pop(0)
        players.append(p)
        return p

    def select_one_move(self):
        percent_wins, move = max(
            (self.wins.get((self.player, move), 0) /
             self.plays.get((self.player, move), 1),
             move)
            for move in self.board.availables)

        return move

    def adjacent_moves(self, board, player, plays):
        """
        adjacent moves without statistics info
        """
        moved = list(set(range(board.width * board.height)) - set(board.availables))
        adjacents = set()
        width = board.width
        height = board.height

        for m in moved:
            h = m // width
            w = m % width
            if w < width - 1:
                adjacents.add(m + 1) # right
            if w > 0:
                adjacents.add(m - 1) # left
            if h < height - 1:
                adjacents.add(m + width) # upper
            if h > 0:
                adjacents.add(m - width) # lower
            if w < width - 1 and h < height - 1:
                adjacents.add(m + width + 1) # upper right
            if w > 0 and h < height - 1:
                adjacents.add(m + width - 1) # upper left
            if w < width - 1 and h > 0:
                adjacents.add(m - width + 1) # lower right
            if w > 0 and h > 0:
                adjacents.add(m - width - 1) # lower left

        adjacents = list(set(adjacents) - set(moved))
        for move in adjacents:
            if plays.get((player, move)):
                adjacents.remove(move)
        return adjacents

    def has_a_winner(self, board):
        moved = list(set(range(board.width * board.height)) - set(board.availables))
        if(len(moved) < self.n_in_row + 2):
            return False, -1

        width = board.width
        height = board.height
        states = board.states
        n = self.n_in_row
        for m in moved:
            h = m // width
            w = m % width
            player = states[m]

            if (w in range(width - n + 1) and
                len(set(states[i] for i in range(m, m + n))) == 1):
                return True, player

            if (h in range(height - n + 1) and
                len(set(states[i] for i in range(m, m + n * width, width))) == 1):
                return True, player

            if (w in range(width - n + 1) and h in range(height - n + 1) and
                len(set(states[i] for i in range(m, m + n * (width + 1), width + 1))) == 1):
                return True, player

            if (w in range(n - 1, width) and h in range(height - n + 1) and
                len(set(states[i] for i in range(m, m + n * (width - 1), width - 1))) == 1):
                return True, player

        return False, -1

    def __str__(self):
        return "AI"