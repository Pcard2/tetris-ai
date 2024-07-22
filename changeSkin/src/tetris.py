
"""
@author: Viet Nguyen <nhviet1009@gmail.com>
"""
import numpy as np
from matplotlib import style
import torch
import random
import pygame
import src.shapes as shapes
import matplotlib.pyplot as plt
from IPython import display

plt.ion()

class Tetris:
    piece_colors = [
        (0, 0, 0),
        (255, 255, 0),
        (147, 88, 254),
        (54, 175, 144),
        (255, 0, 0),
        (102, 217, 238),
        (254, 151, 32),
        (0, 0, 255)
    ]

    pieces = [
        [[1, 1],
         [1, 1]],

        [[0, 2, 0],
         [2, 2, 2]],

        [[0, 3, 3],
         [3, 3, 0]],

        [[4, 4, 0],
         [0, 4, 4]],

        [[5, 5, 5, 5]],

        [[0, 0, 6],
         [6, 6, 6]],

        [[7, 0, 0],
         [7, 7, 7]]
    ]

    def __init__(self, height=20, width=10, block_size=20):
        self.height = height
        self.width = width
        self.block_size = block_size
        self.extra_board = np.ones((self.height * self.block_size, self.width * int(self.block_size / 2), 3),
                                   dtype=np.uint8) * np.array([204, 204, 255], dtype=np.uint8)
        self.text_color = (200, 20, 220)
        self.reset()

        self.bgColor = (95,95,178)
        self.boxColor = (110,130,212)
        self.size = block_size
        self.spacing = 2

        pygame.init()
        self.window = pygame.display.set_mode((288, 338), pygame.SRCALPHA)
        pygame.display.set_caption("Tetris game")

        self.font = pygame.font.SysFont('confortaa', 32)
        self.small_font = pygame.font.SysFont('confortaa', 24)

        self.plot_scores = []
        self.plot_mean_scores = []
        self.total_cleared_lines = []
        self.total_rewards = 0
        

    def reset(self):
        self.board = [[0] * self.width for _ in range(self.height)]
        self.reward = 0
        self.tetrominoes = 0
        self.cleared_lines = 0
        self.bag = list(range(len(self.pieces)))
        random.shuffle(self.bag)
        self.ind = self.bag.pop()
        self.piece = [row[:] for row in self.pieces[self.ind]]
        self.current_pos = {"x": self.width // 2 - len(self.piece[0]) // 2, "y": 0}
        self.gameover = False
        return self.get_state_properties(self.board)

    def rotate(self, piece):
        num_rows_orig = num_cols_new = len(piece)
        num_rows_new = len(piece[0])
        rotated_array = []

        for i in range(num_rows_new):
            new_row = [0] * num_cols_new
            for j in range(num_cols_new):
                new_row[j] = piece[(num_rows_orig - 1) - j][i]
            rotated_array.append(new_row)
        return rotated_array

    def get_state_properties(self, board):
        lines_cleared, board = self.check_cleared_rows(board)
        holes = self.get_holes(board)
        bumpiness, height = self.get_bumpiness_and_height(board)

        return torch.FloatTensor([lines_cleared, holes, bumpiness, height])

    def get_holes(self, board):
        num_holes = 0
        for col in zip(*board):
            row = 0
            while row < self.height and col[row] == 0:
                row += 1
            num_holes += len([x for x in col[row + 1:] if x == 0])
        return num_holes

    def get_bumpiness_and_height(self, board):
        board = np.array(board)
        mask = board != 0
        invert_heights = np.where(mask.any(axis=0), np.argmax(mask, axis=0), self.height)
        heights = self.height - invert_heights
        total_height = np.sum(heights)
        currs = heights[:-1]
        nexts = heights[1:]
        diffs = np.abs(currs - nexts)
        total_bumpiness = np.sum(diffs)
        return total_bumpiness, total_height

    def get_next_states(self):
        states = {}
        piece_id = self.ind
        curr_piece = [row[:] for row in self.piece]
        if piece_id == 0:  # O piece
            num_rotations = 1
        elif piece_id == 2 or piece_id == 3 or piece_id == 4:
            num_rotations = 2
        else:
            num_rotations = 4

        for i in range(num_rotations):
            valid_xs = self.width - len(curr_piece[0])
            for x in range(valid_xs + 1):
                piece = [row[:] for row in curr_piece]
                pos = {"x": x, "y": 0}
                while not self.check_collision(piece, pos):
                    pos["y"] += 1
                self.truncate(piece, pos)
                board = self.store(piece, pos)
                states[(x, i)] = self.get_state_properties(board)
            curr_piece = self.rotate(curr_piece)
        return states

    def get_current_board_state(self):
        board = [x[:] for x in self.board]
        for y in range(len(self.piece)):
            for x in range(len(self.piece[y])):
                board[y + self.current_pos["y"]][x + self.current_pos["x"]] = self.piece[y][x]
        return board

    def new_piece(self):
        if not len(self.bag):
            self.bag = list(range(len(self.pieces)))
            random.shuffle(self.bag)
        self.ind = self.bag.pop()
        self.piece = [row[:] for row in self.pieces[self.ind]]
        self.current_pos = {"x": self.width // 2 - len(self.piece[0]) // 2,
                            "y": 0
                            }
        if self.check_collision(self.piece, self.current_pos):
            self.gameover = True

    def check_collision(self, piece, pos):
        future_y = pos["y"] + 1
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if future_y + y > self.height - 1 or self.board[future_y + y][pos["x"] + x] and piece[y][x]:
                    return True
        return False

    def truncate(self, piece, pos):
        gameover = False
        last_collision_row = -1
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if self.board[pos["y"] + y][pos["x"] + x] and piece[y][x]:
                    if y > last_collision_row:
                        last_collision_row = y

        if pos["y"] - (len(piece) - last_collision_row) < 0 and last_collision_row > -1:
            while last_collision_row >= 0 and len(piece) > 1:
                gameover = True
                last_collision_row = -1
                del piece[0]
                for y in range(len(piece)):
                    for x in range(len(piece[y])):
                        if self.board[pos["y"] + y][pos["x"] + x] and piece[y][x] and y > last_collision_row:
                            last_collision_row = y
        return gameover

    def store(self, piece, pos):
        board = [x[:] for x in self.board]
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if piece[y][x] and not board[y + pos["y"]][x + pos["x"]]:
                    board[y + pos["y"]][x + pos["x"]] = piece[y][x]
        return board

    def check_cleared_rows(self, board):
        to_delete = []
        for i, row in enumerate(board[::-1]):
            if 0 not in row:
                to_delete.append(len(board) - 1 - i)
        if len(to_delete) > 0:
            board = self.remove_row(board, to_delete)
        return len(to_delete), board

    def remove_row(self, board, indices):
        for i in indices[::-1]:
            del board[i]
            board = [[0 for _ in range(self.width)]] + board
        return board

    def step(self, action, epoch):
        x, num_rotations = action
        self.current_pos = {"x": x, "y": 0}
        for _ in range(num_rotations):
            self.piece = self.rotate(self.piece)

        while not self.check_collision(self.piece, self.current_pos):
            self.current_pos["y"] += 1

        overflow = self.truncate(self.piece, self.current_pos)
        if overflow:
            self.gameover = True

        self.board = self.store(self.piece, self.current_pos)
        self.epoch = epoch
        lines_cleared, self.board = self.check_cleared_rows(self.board)
        score = 1 + (lines_cleared ** 2) * self.width
        self.reward += score
        self.tetrominoes += 1
        self.cleared_lines += lines_cleared
        if not self.gameover:
            self.new_piece()
        if self.gameover:
            self.reward -= 2
            # self.plot(epoch)

        return score, self.gameover

    def printGrid(self): # prints the grid line
        for line in self.board:
            print(line)

    def drawGrid(self):    # for every element in the list, it creates a box with the 'size'
        for y in range(len(self.board)):
            for x in range(len(self.board[y])):
                color = shapes.tetrominos_colors[self.board[y][x]] # chooses the color with using the number of the grid block
                x_grid, y_grid = (self.size + self.spacing) * x, (self.size + self.spacing) * y # defines the positions of the grid blocks
                pygame.draw.rect(self.window, color, (x_grid, y_grid, self.size, self.size)) #Rect((left, top), (width, height))
    def drawPoints(self):
        superf_text = self.font.render("Score", True, "white")
        superf_points = self.font.render(f'{int(self.reward)}', True, "white")
        rect_text = superf_text.get_rect()
        rect_points = superf_points.get_rect()
        rect_text.centerx = 228
        rect_points.centerx = 228
        rect_points.centery = 45
        pygame.draw.rect(self.window, self.boxColor, (178, 25, 100, 40), border_radius=5)
        self.window.blit(superf_text, rect_text)
        self.window.blit(superf_points, rect_points)


    def drawNext(self):
        superf_text = self.font.render("Next", True, "white")

        rect_text = superf_text.get_rect()
        rect_text.centerx = 228
        rect_text.centery = 95
        pygame.draw.rect(self.window, self.boxColor, (178, 110, 100, 80), border_radius=5)
        self.drawNextShape(200, 115 + self.spacing)
        self.window.blit(superf_text, rect_text)

    def drawPaused(self):
        superf_text = self.font.render("Paused", True, "black")
        rect_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        rect_surface.fill((255, 255, 255, 100))
        rect_text = superf_text.get_rect()
        rect_text.center = self.width//2, self.height//2
        self.window.blit(rect_surface, (0, 0))
        self.window.blit(superf_text, rect_text)

    def drawInfo(self, epoch):
        superf_text1 = self.small_font.render(f"# Games: {epoch}", True, "white")
        superf_text2 = self.small_font.render(f"Reward: {self.reward}", True, "white")
        superf_text3 = self.small_font.render(f"Lines: {self.cleared_lines}", True, "white")
        rect_text1 = superf_text1.get_rect()
        rect_text1.x = 178
        rect_text1.centery = 220
        rect_text2 = superf_text2.get_rect()
        rect_text2.x = 178
        rect_text2.centery = 250
        rect_text3 = superf_text3.get_rect()
        rect_text3.x = 178
        rect_text3.centery = 280
        self.window.blit(superf_text1, rect_text1)
        self.window.blit(superf_text2, rect_text2)
        self.window.blit(superf_text3, rect_text3)

    def drawNextShape(self, xs,ys):
        shape = self.piece

        for y in range(len(shape)):
            for x in range(len(shape[y])):
                x_grid, y_grid = (self.size + self.spacing) * x + xs, (self.size + self.spacing) * y + ys # defines the positions of the grid blocks
                color = shapes.tetrominos_colors[shape[y][x]] # chooses the color with using the number of the grid block
                if not shape[y][x] == 0:
                    pygame.draw.rect(self.window, color, (x_grid, y_grid, self.size, self.size)) #Rect((left, top), (width, height)) 

    def render(self, epoch):

        self.window.fill(self.bgColor)
        self.drawPoints()
        self.drawNext()
        self.drawGrid()
        self.drawInfo(epoch)

        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

        pygame.display.update()



    def plot(self):
        self.plot_scores.append(self.reward)
        self.total_rewards += self.reward
        self.mean_score = self.total_rewards / self.epoch
        self.total_rewards_10 = sum(self.plot_scores[-10:])
        self.mean_score_10 = self.total_rewards_10 / 10
        self.plot_mean_scores.append(self.mean_score)
        self.total_cleared_lines.append(self.cleared_lines)

        display.clear_output(wait=True)
        display.display(plt.gcf())
        plt.clf()
        plt.title('Training...')
        plt.xlabel('Number of Games')
        plt.ylabel('Reward')
        plt.plot(self.plot_scores, color="tab:blue")
        plt.plot(self.plot_mean_scores, color="tab:red")
        plt.plot(self.total_cleared_lines, color="tab:green")
        plt.ylim(ymin=0)
        plt.text(len(self.plot_scores)-1, self.plot_scores[-1], str(self.plot_scores[-1]))
        plt.text(len(self.plot_mean_scores)-1, self.plot_mean_scores[-1], str(self.plot_mean_scores[-1]))
        plt.text(len(self.total_cleared_lines)-1, self.total_cleared_lines[-1], str(self.total_cleared_lines[-1]))
        plt.show(block=False)
        plt.pause(.1)

    def saveGraph(self, num):
        plt.savefig(f"graph{num}.svg")