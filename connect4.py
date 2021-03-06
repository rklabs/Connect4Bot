"""
Connect4 is an implementation of Connect4 game.
The board is 7x6 and is maintaind using 2D list.
Each block in the board can be player_a or player_b
or empty_block which are represented using 'X', 'O'
and '*' respectively. Winner is determined by checking
4 directions(horizontal, vertical, diagonal(/),
diagonal(\)) in the 2D list. This game can be
independently run on the terminal.
"""
import random
import functools
import time

STEP_DELAY = 1  # second(s)


class Connect4:

    def __init__(self):
        self.connect4_board = []
        self.player_a = 'X'
        self.player_b = 'O'
        self.empty_block = '*'
        self.board_width = 7
        self.board_height = 6

    def build_new_board(self):
        """Build new game board with empty blocks"""
        self.connect4_board = []

        for _ in range(self.board_height):
            self.connect4_board.append([self.empty_block] * (self.board_width))

    def rows(self):
        """Return each row of the 2D list as generator"""
        for row in self.connect4_board:
            yield row

    def print_board(self):
        """Print the current board state"""
        print('Current board')

        for row in self.connect4_board:
            print('|'.join(row))

    def choose_first_player(self):
        """Randomnly choose the first player for game simluation"""
        return random.choice([self.player_a, self.player_b])

    def make_move(self, player, column):
        """Choose empty block in column"""
        row = self.board_height - 1

        while row > 0 and \
            (self.connect4_board[row][column] == self.player_a or
             self.connect4_board[row][column] == self.player_b):

            row -= 1

        self.connect4_board[row][column] = player

        return True

    def choose_random_column(self):
        """Choose random column for game simulation"""
        return random.randint(0, self.board_width - 1)

    def is_board_full(self):
        """Check if board is full(tie)"""
        cnt = 0

        for x in range(self.board_height):
            for y in range(self.board_width):
                if self.connect4_board[x][y] == self.player_a or \
                        self.connect4_board[x][y] == self.player_b:
                    cnt += 1

        return cnt == (self.board_width * self.board_height)

    def check_row(self, player):
        """Check all rows in board for four continuous blocks"""
        # Check rows for 4 continuous self.player_a or self.player_b
        for y in range(self.board_width):
            for x in range(self.board_height - 3):
                if self.connect4_board[x][y] == player and \
                        self.connect4_board[x + 1][y] == player and \
                        self.connect4_board[x + 2][y] == player and \
                        self.connect4_board[x + 3][y] == player:
                    return True

    def check_column(self, player):
        """Check all columns in board for four continuous blocks"""
        # Check columns for 4 continuous self.player_a or self.player_b
        for x in range(self.board_height):
            for y in range(self.board_width - 3):
                if self.connect4_board[x][y] == player and \
                        self.connect4_board[x][y + 1] == player and \
                        self.connect4_board[x][y + 2] == player and \
                        self.connect4_board[x][y + 3] == player:
                    return True

    def check_diagonal_left_to_right(self, player):
        """Check all diagonals(\) in board for four continuous blocks"""
        # Check diagonal for 4 continuous self.player_a or self.player_b
        # Diagonal from top right to bottom left
        for x in range(self.board_height - 3):
            for y in range(3, self.board_width - 1):
                if self.connect4_board[x][y] == player and \
                        self.connect4_board[x + 1][y - 1] == player and \
                        self.connect4_board[x + 2][y - 2] == player and \
                        self.connect4_board[x + 3][y - 3] == player:
                    return True

    def check_diagonal_right_to_left(self, player):
        """Check all diagonals(/) in board for four continuous blocks"""
        # Diagonal from top left to bottom right
        for x in range(self.board_height - 3):
            for y in range(self.board_width - 3):
                if self.connect4_board[x][y] == player and \
                        self.connect4_board[x + 1][y + 1] == player and \
                        self.connect4_board[x + 2][y + 2] == player and \
                        self.connect4_board[x + 3][y + 3] == player:
                    return True

    def check_winner(self, player):
        """Check all 4 directions for continuous similar blocks"""
        winner_check_funcs = [functools.partial(self.check_row, player),
                              functools.partial(self.check_column, player),
                              functools.partial(
                                  self.check_diagonal_left_to_right, player),
                              functools.partial(
                                  self.check_diagonal_right_to_left, player)]

        for func in winner_check_funcs:
            if func():
                return True

        # Winner not found
        return False

    def is_column_full(self, column):
        """Check if column is full(and does not have empty block)"""
        column_elements = map(lambda row: row[column], self.connect4_board)
        empty_elements = filter(lambda elem: elem == self.empty_block,
                                column_elements)

        return False if len(empty_elements) > 0 else True


def main():
    connect4 = Connect4()
    player = connect4.choose_first_player()

    connect4.build_new_board()

    connect4.print_board()

    while True:
        column = connect4.choose_random_column()

        # If column is full choose another column
        if connect4.is_column_full(column) and \
                not connect4.is_board_full():
            continue

        print('Player {} column {}'.format(player, column))

        connect4.make_move(player, column)

        connect4.print_board()

        if connect4.check_winner(player):
            print('Player {} won!'.format(player))
            return True

        if connect4.is_board_full():
            print('It\'s a tie!')
            return True

        # Make sure each player gets his / her turn
        # in alternative fashion
        if player == connect4.player_a:
            player = connect4.player_b
        elif player == connect4.player_b:
            player = connect4.player_a

        time.sleep(STEP_DELAY)

if __name__ == '__main__':
    main()
