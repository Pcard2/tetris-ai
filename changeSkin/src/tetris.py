
"""
@author: Viet Nguyen <nhviet1009@gmail.com>
edited by: Pau Cardona
"""

version = "24-AI"

import numpy as np
import torch
import random
import pygame
import matplotlib.pyplot as plt
import gspread
from time import time

plt.ion()
plt.style.use('ggplot')

class Tetris:
    piece_colors = [
        (0, 0, 0),
        (225, 225, 0),
        (147, 88, 254),
        (54, 175, 144),
        (255, 0, 0),
        (102, 217, 238),
        (254, 151, 32),
        (0, 0, 205)
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
        self.holes = 0
        self.reset()

        self.bgColor = (95,95,178)
        self.boxColor = (110,130,212)
        self.size = block_size
        self.spacing = 2

        self.points = 0
        pygame.init()
        xs, ys = 288, 388
        self.window = pygame.display.set_mode((xs, ys), pygame.SRCALPHA)
        pygame.display.set_caption("Tetris game")

        self.font = pygame.font.SysFont('confortaa', 32)
        self.small_font = pygame.font.SysFont('confortaa', 24)

        self.plot_scores = []
        self.plot_mean_scores = []
        self.total_cleared_lines = []
        self.total_rewards = 0

        self.gameTime = time()
        self.hi_score = 0
        self.stats = {
            "version": version,
            "timePlayed": 0,
            "points": 0,
            "pointsHistory": [],
            "linesCleared": 0,
            "windowStats": {"gridSize": (self.width, self.height), "screenSize": (xs, ys)},
            "totalPieces": 0,
        }
        

    def reset(self):
        self.board = [[0] * self.width for _ in range(self.height)]
        self.reward = 0
        self.tetrominoes = 0
        self.points = 0
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

        
        # self.reward += self.holes - holes
        # self.holes = holes

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
        score = self.scoring(lines_cleared)
        self.reward += score
        self.tetrominoes += 1
        self.cleared_lines += lines_cleared
        if not self.gameover:
            self.new_piece()
        if self.gameover:
            self.reward -= 2
            self.plot()
            if self.hi_score < self.points:
                self.hi_score = self.points

        return score, self.gameover

    def printGrid(self): # prints the grid line
        for line in self.board:
            print(line)

    def drawGrid(self):    # for every element in the list, it creates a box with the 'size'
        for y in range(len(self.board)):
            for x in range(len(self.board[y])):
                color = self.piece_colors[self.board[y][x]] # chooses the color with using the number of the grid block
                x_grid, y_grid = (self.size + self.spacing) * x, (self.size + self.spacing) * y # defines the positions of the grid blocks
                pygame.draw.rect(self.window, color, (x_grid, y_grid, self.size, self.size)) #Rect((left, top), (width, height))
    
    def drawPoints(self):
        superf_text = self.font.render("Score", True, "white")
        superf_points = self.font.render(f'{int(self.points)}', True, "white")
        rect_text = superf_text.get_rect()
        rect_points = superf_points.get_rect()
        rect_text.centerx = 228
        rect_points.centerx = 228
        rect_points.centery = 45
        pygame.draw.rect(self.window, self.boxColor, (178, 25, 100, 40), border_radius=5)
        self.window.blit(superf_text, rect_text)
        self.window.blit(superf_points, rect_points)

    def drawReward(self):
        superf_text = self.font.render("Reward", True, "white")
        superf_points = self.font.render(f'{int(self.reward)}', True, "white")
        rect_text = superf_text.get_rect()
        rect_points = superf_points.get_rect()
        rect_text.centerx = 228
        rect_text.centery = 80
        rect_points.centerx = 228
        rect_points.centery = 115
        pygame.draw.rect(self.window, self.boxColor, (178, 95, 100, 40), border_radius=5)
        self.window.blit(superf_text, rect_text)
        self.window.blit(superf_points, rect_points)


    def drawNext(self):
        superf_text = self.font.render("Next", True, "white")

        rect_text = superf_text.get_rect()
        rect_text.centerx = 228
        rect_text.centery = 150
        pygame.draw.rect(self.window, self.boxColor, (178, 165, 100, 80), border_radius=5)
        self.drawNextShape(200, 168 + self.spacing)
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
        superf_text2 = self.small_font.render(f"Lines: {self.cleared_lines}", True, "white")
        superf_text3 = self.small_font.render(f"Hi-score: {self.hi_score}", True, "white")
        rect_text1 = superf_text1.get_rect()
        rect_text1.x = 178
        rect_text1.centery = 275
        rect_text2 = superf_text2.get_rect()
        rect_text2.x = 178
        rect_text2.centery = 305
        rect_text3 = superf_text3.get_rect()
        rect_text3.x = 178
        rect_text3.centery = 335
        self.window.blit(superf_text1, rect_text1)
        self.window.blit(superf_text2, rect_text2)
        self.window.blit(superf_text3, rect_text3)

    def drawNextShape(self, xs,ys):
        shape = self.piece

        for y in range(len(shape)):
            for x in range(len(shape[y])):
                x_grid, y_grid = (self.size + self.spacing) * x + xs, (self.size + self.spacing) * y + ys # defines the positions of the grid blocks
                color = self.piece_colors[shape[y][x]] # chooses the color with using the number of the grid block
                if not shape[y][x] == 0:
                    pygame.draw.rect(self.window, color, (x_grid, y_grid, self.size, self.size)) #Rect((left, top), (width, height)) 

    def scoring(self, lines_cleared):
        reward = 0
        comboCount = 0
        if lines_cleared > 0:
            comboCount += 1
            match lines_cleared:
                case 1: # Single
                    self.points += 100
                    self.stats["pointsHistory"].append("1LINE") ## STAT
                    reward += 1
                case 2: # Double
                    self.stats["pointsHistory"].append("2LINES") ## STAT
                    self.points += 200
                    reward += 2
                case 3: # Triple
                    self.stats["pointsHistory"].append("3LINES") ## STAT
                    self.points += 400
                    reward += 4
                case 4: # Tetris
                    self.stats["pointsHistory"].append("4LINES") ## STAT
                    self.points += 800
                    reward += 8
            if comboCount > 1:
                self.points *= 1.5
                comboCount += 1
        else:
            comboCount = 1
        score = comboCount + reward * self.width
        return score

    def uploadStats(self):
        print("[DEBUG] SAVING STATS...")

        self.stats["points"] = self.points ## STAT
        self.stats["timePlayed"] = time() - self.gameTime ## STAT
        self.stats["points"] = self.points
        self.stats["linesCleared"] = self.cleared_lines
        self.stats["totalPieces"] = self.tetrominoes

        ## gspread
        credentials = {
            "type": "service_account",
            "project_id": "tetris-tdr",
            "private_key_id": "5894339241a935a22bc8530dd935698eb570612f",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDIFe3wqbC6KlY8\nOodNRQPNEPlZiXzJyeVfS7lT/H5Gt8G9c1f507Lu24P+qZmx4ApNr5LyiHgbLYTq\nJLfCsLKIHEFP3PTSkJKG+Y+hjVZIKlZvIhe2j27J3LHeANg55FHM59lXO7U2IPxK\nY75HxBo9pimfBukDX6XiNt7D95irpCr56Nxdj98B4IkNAvoOWTozCh3hnRNT72Yf\nuKLl+8g5dOj4aS0C2QHH1bT2mlG+I1YJeDkZNAPfqGp1mG4yUqcoSbdfW1UQqhgw\nkPpdJAGTVXac3u8PXc5LdM42iUpKyEiA25ppv9+oE6uhi+2LjnFunUx5Fo4q54EW\ncKHQLGp7AgMBAAECggEAA8/LIyEQcVN6JhaVWkb8zgzLO0XvvyZd/MVECBIQ08cP\nZU0LuYIrb/p1lsXjXCyg9Z7pJT6tTxM8a3t8lrRoCkjDg8J5VYOUjwa1EkZPhPtt\nfxt+qSctXKIcL1cDx4KOfmFSViOYjanuNHqW9uYI+/Cs7U8j5EEPt3IFJ2WRnn9u\n/wezuMS9medFO0ZT8q5tjIH8kq5qQ2MKYHW/CSD1UWNDIgv+YCaC7tYBheiF4dj7\nBpUfqfGNNOUphfYDjKen//5UoJuOxRl/zvxVap3P+/O7bEAsziWw8/HX5J6dNXi9\n18BiZwgtJqNcaimYYYh5BRGJYUCknHVTj7/BpRmAsQKBgQDzBvHJHjp/RJ0M9riU\ntp2hladFuNL7yFk5nSBNqIvP12sAZnyV63U2D0XVTg35FFJBtry+Az9nWW2E28Sm\npY9iQyx6IZ0x7EzmAvMAk10jyv7DXElssnizhapbLjyjre3pwJys7POGSHUFtEYO\nMomVCYf987TXQGSBddH3jX3N8QKBgQDSxCyKYpvvwS+RTNIXN9+jFdfou89U/0XY\nIjK7yeUqPaBodJOduc85CrIK8NFI5r5X+bYznQlkjsQxIpXae2Tqip8CM1mWWH46\nLZaC+WcxFF3MyLbrloN7bIj4bCfHGE0HZxtSFGnjtxHFS0jWMmXWPCo7ZHeUcpKT\n9ngJH7EDKwKBgQCgufQIbfyEFQ3E+BsFB21i40W4X87xhAQ2jUtC8PheYfq7TgyR\nXiKruRgXRUMKez0XhtJ23FD/ee5rkqkRCae1dfWhZD/BN6V37XVm6Q8NUACDlbJd\nt/8Jw5nyKbcjDTGuiZtU5nT8V0lFl39JfnTtY1tUQexU+5o84H4XubT9EQKBgEpV\nmgfso2a50dcDKw25TQytxYp1wrgNmEqUNSR6HnL5bTup8e4s/GL33LdzG70EdJl+\nnr4xYoCuwY86zXNTFdKKtW4HQk9+QnauYWksITL0Jej12V3ZpeG/88b6DkVv0qsL\nuF0IihggFwpodPXmrHgUnCh6VJpsljnNMaS2Iq4lAoGAJCzvDUJXDXNvcCFWMHrH\nEpFw3LwNlB3VuXJoc5QFHX/tZvzOxMldfXzo7widthfy3x4EGqA25DbBKHGfvlwWUqJ\na5IjlN2wXOdjOZ9Ks+VVc4fA1IcHqqCyvcSwfe89gYOCpTIBPhUw2H8T/47cP2GI\nwJEGfVeDPaVLjfdydfwpnQ8=\n-----END PRIVATE KEY-----\n",
            "client_email": "tetris-tdr@tetris-tdr.iam.gserviceaccount.com",
            "client_id": "100570209494388998451",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tetris-tdr%40tetris-tdr.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open("Python Game Playtesters")
        wks = sh.worksheet("AI")

        i=2
        while wks.get('A'+str(i))[0] != []: # while empty cell value
            i+=1

        stats_list = []
        for a in self.stats:
            stats_list.append(str(self.stats[a]))
            
        wks.update('A'+str(i), [stats_list])
        print("[DEBUG] SAVED STATS!")

    def render(self, epoch):
        self.printGrid()

        self.window.fill(self.bgColor)
        self.drawPoints()
        self.drawReward()
        self.drawNext()
        self.drawInfo(epoch)
        self.drawGrid()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # self.uploadStats()
                pygame.quit()
                quit()

        pygame.display.update()

    def plot(self):
        self.total_rewards += self.reward
        self.plot_scores.append(self.reward)
        # self.mean_score = sum(self.plot_scores[-100:]) / 100  # mean scores of last 100 games
        self.mean_score = self.total_rewards / self.epoch
        self.plot_mean_scores.append(self.mean_score)
        # self.total_cleared_lines.append(self.cleared_lines)

        plt.clf()
        plt.title(f'Epoch: {self.epoch}')
        plt.xlabel('Number of Games')
        plt.ylabel('Reward')
        plt.plot(self.plot_scores, color="tab:blue")
        plt.plot(self.plot_mean_scores, color="tab:red")
        # plt.plot(self.total_cleared_lines, color="tab:green")
        plt.ylim(ymin=0)
        plt.text(len(self.plot_scores)-1, self.plot_scores[-1], str(self.plot_scores[-1]))
        plt.text(len(self.plot_mean_scores)-1, self.plot_mean_scores[-1], str(self.plot_mean_scores[-1]))
        # plt.text(len(self.total_cleared_lines)-1, self.total_cleared_lines[-1], str(self.total_cleared_lines[-1]))
        plt.show(block=False)
        plt.pause(.1)

    def saveGraph(self, num):
        plt.savefig(f"trained_models/graph{num}.svg")