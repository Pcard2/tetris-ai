# inspired by 

from  shapes import *
import pygame
import random
from datetime import datetime ## FOR PLAYER GAME
import gspread ## SPREADSHEETS
import torch

version = "23-modified"
        
##############################    MAIN    ##############################

class Tetris():
    ##############################    INICIALIZATION    ##############################

    def createGrid(self, width, height):
        # global grid
        for y in range(height):
            self.grid.append([])
            for _ in range(width):
                self.grid[y].append(0)
        return self.grid

    #############################################################################

    def __init__(self, width=10, height=20, block_size=15):
        ### CUSTOMIZE ###
        self.MOVE_SPEED = 80
        self.ROTATE_SPEED = 100
        self.FALL_SPEED = 270
        #################

        self.height = height
        self.width = width
        self.size = block_size

        self.grid = []

        self.xs, self.ys = 288,338
        self.bgColor = (95,95,178)
        self.boxColor = (110,130,212)
        self.spacing = 2

        pygame.init()
        self.window = pygame.display.set_mode((self.xs, self.ys), pygame.SRCALPHA)
        pygame.display.set_caption("Tetris game")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont('confortaa', 32)

        
        self.createGrid(width, height)

        self.executant = True
        self.points = 0
        self.comboCount = 1
        self.gameTime = time()
        self.moveTime = 0
        self.fallTime = 0
        self.stats = {
            "version": version,
            "dateTime": "",
            "timePlayed": 0,
            "points": 0,
            "pointsHistory": [],
            "linesCleared": 0,
            "windowStats": {"gridSize": (self.width, self.height), "screenSize": (self.xs, self.ys)},
            "controlHistory": [],
            "totalPieces": 0,
            "pieceHistory": [],
        }
        self.movement = {"up": False, "left": False, "down": False, "right": False}

        self.piece, self.shapeChar= self.newShape()
        self.nextShape, self.nextShapeChar = self.newShape()
        self.currentRotation = 0
        self.paused = False
        self.gameover = False
        self.reward = 0
        self.linesCleared = 0
    def drawGrid(self):    # for every element in the list, it creates a box with the 'size'
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                color = tetrominos_colors[self.grid[y][x]] # chooses the color with using the number of the grid block
                x_grid, y_grid = (self.size + self.spacing) * x, (self.size + self.spacing) * y # defines the positions of the grid blocks
                pygame.draw.rect(self.window, color, (x_grid, y_grid, self.size, self.size)) #Rect((left, top), (width, height)) 

    def printGrid(self): # prints the grid line
        for line in self.grid:
            print(line)

    def check_cleared_rows(self): # looks at every line in the gridand, if every space is occupied, it clears the line anc creates a new one
        lines_cleared = 0
        for y in range(len(self.grid)):
            if not 0 in self.grid[y]:
                for yReplace in range(y, 0, -1): # start:y end:0 step:-1
                    self.grid[yReplace] = self.grid[yReplace-1]
                self.grid[0] = [0] * len(self.grid[0]) # defines first line to be clear because of a bug where pieces stretch
                self.stats["linesCleared"] += 1 ## STAT
                lines_cleared += 1
                
        return lines_cleared, self.grid

    def scoring(self):
        actionPoints = 0
        if self.linesCleared > 0:
            comboCount += 1
            match self.linesCleared:
                case 1: # Single
                    if self.shapeChar == "T" and self.collisionShape(self.grid, self.piece, self.currentRotation, self.current_pos["x"], self.current_pos["y"]-1):
                        self.stats["pointsHistory"].append("T-SPIN 1-LINE") ## STAT
                        actionPoints += 800
                        self.reward = 3
                    else:
                        actionPoints += 100
                        self.stats["pointsHistory"].append("1LINE") ## STAT
                        self.reward = 1
                case 2: # Double
                    if self.shapeChar == "T" and self.collisionShape(self.grid, self.piece, self.currentRotation, self.current_pos["x"], self.current_pos["y"]-1):
                        self.stats["pointsHistory"].append("T-SPIN 2-LINES") ## STAT
                        actionPoints += 100
                        self.reward += 6
                    else:
                        self.stats["pointsHistory"].append("2LINES") ## STAT
                        actionPoints += 1200
                        self.reward += 2
                case 3: # Triple
                    if self.shapeChar == "T" and self.collisionShape(self.grid, self.piece, self.currentRotation, self.current_pos["x"], self.current_pos["y"]-1):
                        self.stats["pointsHistory"].append("T-SPIN 3-LINES") ## STAT
                        actionPoints += 1600
                        self.reward += 10
                    else:
                        self.stats["pointsHistory"].append("3LINES") ## STAT
                        actionPoints += 500
                        self.reward += 3
                case 4: # Tetris
                    self.stats["pointsHistory"].append("4LINES") ## STAT
                    actionPoints += 800
                    self.reward += 6
            if comboCount > 1:
                actionPoints *= 1.5
                self.reward += 1
        else:
            comboCount = 1

        return self.points + actionPoints

    def newShape(self):
        shapeNum = random.randint(0, len(tetrominosStr)-1)
        shape = tetrominos[shapeNum]
        shapeChar = tetrominosStr[shapeNum]
        
        return shape, shapeChar

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

    def drawDebug(self):
        superf_text = self.font.render(f"{self.clock.get_fps():.0f}", True, "black")
        rect_text = superf_text.get_rect()
        rect_text.centerx = 228
        rect_text.centery = 300
        self.window.blit(superf_text, rect_text)

    def replacePos(self,x,y,val):
        self.grid[y][x] = val

    def drawShape(self, x, y):
        shape = self.piece[self.currentRotation]
        
        xb = -1
        yb = -1
        for shapeY in shape:
            yb += 1
            xb = -1
            for shapePiece in shapeY:
                xb += 1
                if shapePiece != 0: # switch case is slower 13/5/24  https://www.andrewjmoodie.com/blog/2018/09-04-2018-matlab-speed-comparison-of-switch-case-and-if-then-statements-and-hard-code/#:~:text=It%20turns%20out%20that%20switch,then%20or%20case%2Dswitch%20statement.
                    self.replacePos(x+xb,y+yb,shapePiece)
        
    def drawNextShape(self, xs,ys):
        shape = self.piece[self.currentRotation]

        for y in range(len(shape)):
            for x in range(len(shape[y])):
                x_grid, y_grid = (self.size + self.spacing) * x + xs, (self.size + self.spacing) * y + ys # defines the positions of the grid blocks
                color = tetrominos_colors[shape[y][x]] # chooses the color with using the number of the grid block
                if not shape[y][x] == 0:
                    pygame.draw.rect(self.window, color, (x_grid, y_grid, self.size, self.size)) #Rect((left, top), (width, height)) 
        
        
        # for shapeY in shape:
        #     for shapePiece in shapeY:
        #         if shapePiece != 0: # switch case is slower 13/5/24  https://www.andrewjmoodie.com/blog/2018/09-04-2018-matlab-speed-comparison-of-switch-case-and-if-then-statements-and-hard-code/#:~:text=It%20turns%20out%20that%20switch,then%20or%20case%2Dswitch%20statement.
        #             replacePos(grid,x+xb,y+yb,shapePiece)

    # def clearShape(self,x,y):
    #     shape = self.piece[self.currentRotation]
        
    #     yb = -1
    #     for shapeY in shape:
    #         yb += 1
    #         xb = -1
    #         for shapePiece in shapeY:
    #             xb += 1
    #             if shapePiece != 0:
    #                 self.replacePos(x+xb,y+yb,0)

    def reset(self):
        for line in range(len(self.grid)):
            self.grid[line] = [0] * len(self.grid[0])
        self.points = 0
        self.xp,self.yp = self.width//2, 0
        self.currentRotation = 0
        self.cleared_lines = 0
        self.gameover = False
        print("[DEBUG] RESET")
        return self.get_state_properties(self.grid)

    def get_next_states(self):
        states = {}
        curr_piece = [row[:] for row in self.piece]

        for i in range(4):
            valid_xs = self.width - len(curr_piece[0])
            for x in range(valid_xs + 1):
                piece = curr_piece[i] # i - current rotation
                print(1)
                pos = {"x": x, "y": 0}
                while not self.check_collision(piece, pos):
                    pos["y"] += 1
                self.truncate(piece, pos)
                grid = self.store(piece, pos)
                states[(x, i)] = self.get_state_properties(grid)
        return states

    def collisionShape(self, x, y):
        shape = self.piece[self.currentRotation]

        yb = -1
        for shapeY in shape:
            yb += 1
            xb = -1
            for shapePiece in shapeY:
                xb += 1
                if shapePiece != 0:
                    try:
                        if self.grid[y+yb][x+xb] != 0:
                            return True
                        if x+xb < 0:
                            return True
                    except:
                        return True
        return False

    def check_collision(self, piece, pos):
        future_y = pos["y"] + 1
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                self.printGrid()
                if future_y + y > self.height - 1 or self.grid[future_y + y][pos["x"] + x] and piece[y][x]:
                    return True
        return False

    def get_state_properties(self, grid):
        holes = self.get_holes(grid)
        bumpiness, height = self.get_bumpiness_and_height(grid)

        return torch.FloatTensor([self.linesCleared, holes, bumpiness, height])

    def get_holes(self, grid):
        num_holes = 0
        for col in zip(*grid):
            row = 0
            while row < self.width and col[row] == 0:
                row += 1
            num_holes += len([x for x in col[row + 1:] if x >= 0])
        return num_holes

    def get_bumpiness_and_height(self, grid):
        grid = torch.tensor(grid)
        mask = grid != 0
        invert_heights = torch.where(mask.any(axis=0), torch.argmax(mask.to(torch.float32), axis=0), self.height)
        heights = self.height - invert_heights
        total_height = torch.sum(heights)
        currs = heights[:-1]
        nexts = heights[1:]
        diffs = torch.abs(currs - nexts)
        total_bumpiness = torch.sum(diffs)
        return total_bumpiness, total_height

    def truncate(self, piece, pos):
        gameover = False
        last_collision_row = -1
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if self.grid[pos["y"] + y][pos["x"] + x] and piece[y][x]:
                    if y > last_collision_row:
                        last_collision_row = y

        if pos["y"] - (len(piece) - last_collision_row) < 0 and last_collision_row > -1:
            while last_collision_row >= 0 and len(piece) > 1:
                gameover = True
                last_collision_row = -1
                del piece[0]
                print(2)
                for y in range(len(piece)):
                    for x in range(len(piece[y])):
                        if self.grid[pos["y"] + y][pos["x"] + x] and piece[y][x] and y > last_collision_row:
                            last_collision_row = y
        return gameover

    def store(self, piece, pos):
        grid = [x[:] for x in self.grid]
        for y in range(len(piece)):
            for x in range(len(piece[y])):
                if piece[y][x] and not grid[y + pos["y"]][x + pos["x"]]:
                    grid[y + pos["y"]][x + pos["x"]] = piece[y][x]
        return grid

    def uploadStats(stats):
        print("[DEBUG] SAVING STATS...")
        ## gspread
        credentials = {
        "type": "service_account",
        "project_id": "tetris-tdr",
        "private_key_id": "5894339241a935a22bc8530dd935698eb570612f",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDIFe3wqbC6KlY8\nOodNRQPNEPlZiXzJyeVfS7lT/H5Gt8G9c1f507Lu24P+qZmx4ApNr5LyiHgbLYTq\nJLfCsLKIHEFP3PTSkJKG+Y+hjVZIKlZvIhe2j27J3LHeANg55FHM59lXO7U2IPxK\nY75HxBo9pimfBukDX6XiNt7D95irpCr56Nxdj98B4IkNAvoOWTozCh3hnRNT72Yf\nuKLl+8g5dOj4aS0C2QHH1bT2mlG+I1YJeDkZNAPfqGp1mG4yUqcoSbdfW1UQqhgw\nkPpdJAGTVXac3u8PXc5LdM42iUpKyEiA25ppv9+oE6uhi+2LjnFunUx5Fo4q54EW\ncKHQLGp7AgMBAAECggEAA8/LIyEQcVN6JhaVWkb8zgzLO0XvvyZd/MVECBIQ08cP\nZU0LuYIrb/p1lsXjXCyg9Z7pJT6tTxM8a3t8lrRoCkjDg8J5VYOUjwa1EkZPhPtt\nfxt+qSctXKIcL1cDx4KOfmFSViOYjanuNHqW9uYI+/Cs7U8j5EEPt3IFJ2WRnn9u\n/wezuMS9medFO0ZT8q5tjIH8kq5qQ2MKYHW/CSD1UWNDIgv+YCaC7tYBheiF4dj7\nBpUfqfGNNOUphfYDjKen//5UoJuOxRl/zvxVap3P+/O7bEAsziWw8/HX5J6dNXi9\n18BiZwgtJqNcaimYYYh5BRGJYUCknHVTj7/BpRmAsQKBgQDzBvHJHjp/RJ0M9riU\ntp2hladFuNL7yFk5nSBNqIvP12sAZnyV63U2D0XVTg35FFJBtry+Az9nWW2E28Sm\npY9iQyx6IZ0x7EzmAvMAk10jyv7DXElssnizhapbLjyjre3pwJys7POGSHUFtEYO\nMomVCYf987TXQGSBddH3jX3N8QKBgQDSxCyKYpvvwS+RTNIXN9+jFdfou89U/0XY\nIjK7yeUqPaBodJOduc85CrIK8NFI5r5X+bYznQlkjsQxIpXae2Tqip8CM1mWWH46\nLZaC+WcxFF3MyLbrloN7bIj4bCfHGE0HZxtSFGnjtxHFS0jWMmXWPCo7ZHeUcpKT\n9ngJH7EDKwKBgQCgufQIbfyEFQ3E+BsFB21i40W4X87xhAQ2jUtC8PheYfq7TgyR\nXiKruRgXRUMKez0XhtJ23FD/ee5rkqkRCae1dfWhZD/BN6V37XVm6Q8NUACDlbJd\nt/8Jw5nyKbcjDTGuiZtU5nT8V0lFl39JfnTtY1tUQexU+5o84H4XubT9EQKBgEpV\nmgfso2a50dcDKw25TQytxYp1wrgNmEqUNSR6HnL5bTup8e4s/GL33LdzG70EdJl+\nnr4xYoCuwY86zXNTFdKKtW4HQk9+QnauYWksITL0Jej12V3ZpeG/88b6DkVv0qsL\nuF0IihggFwpodPXmrHgUnCh6VJpsljnNMaS2Iq4lAoGAJCzvDUJXDXNvcCFWMHrH\nEpFw3LwNlB3VuXJoc5QFHX/tZvzOxMldfXzo7Xgfy3x4EGqA25DbBKHGfvlwWUqJ\na5IjlN2wXOdjOZ9Ks+VVc4fA1IcHqqCyvcSwfe89gYOCpTIBPhUw2H8T/47cP2GI\nwJEGfVeDPaVLjfdydfwpnQ8=\n-----END PRIVATE KEY-----\n",
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
        for a in stats:
            stats_list.append(str(stats[a]))
            
        wks.update('A'+str(i), [stats_list])
        print("[DEBUG] SAVED STATS!")


    ###################################################################

    # def step(self):
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             pygame.quit()
    #             quit()

    #     self.fallTime += self.clock.get_rawtime()
    #     self.clock.tick()

    #     self.clearShape(self.xp, self.yp)
        
    #     if self.fallTime > self.FALL_SPEED:
    #         self.fallTime = 0
    #         self.yp += 1
    #         if self.collisionShape(self.xp,self.yp): # if the shape collides in the next 
    #             self.changePiece = True
    #             self.yp -= 1

    #     if self.movement["up"]:
    #         self.stats["controlHistory"] += "W" ## CONTROL STAT
    #         self.currentRotation += 1
    #         if self.currentRotation > 3:
    #             self.currentRotation = 0
    #         while self.collisionShape(self.xp,self.yp):
    #             self.currentRotation -= 1

    #     if self.movement['left']:
    #         self.stats["controlHistory"] += "A" ## CONTROL STAT
    #         self.xp -= 1
    #         if self.collisionShape(self.xp, self.yp):
    #             self.xp += 1

    #     if self.movement['down']:
    #         self.stats["controlHistory"] += "S" ## CONTROL STAT
    #         self.yp += 1
    #         if self.collisionShape(self.xp, self.yp): # if the shape collides in the next
    #             self.changePiece = True
    #             self.yp -= 1
                    
            
    #     if self.movement['right']:
    #         self.stats["controlHistory"] += "D" ## CONTROL STAT
    #         self.xp += 1
    #         if self.collisionShape(self.xp, self.yp):
    #             self.xp -= 1
    #         self.movement['right'] == False

        ########################################
        
        

    def new_piece(self):
        self.stats["totalPieces"] += 1 ## STAT
        self.stats["pieceHistory"].append(self.shapeChar) ## STAT
        self.piece, self.shapeChar = self.nextShape, self.nextShapeChar
        self.nextShape, self.extShapeChar = self.newShape()
        self.points = self.scoring()
        self.current_pos = {"x": self.width // 2 - len(self.piece[0]) // 2,
                            "y": 0}

    def step(self, action):
        pygame.display.update()

        x, num_rotations = action
        self.current_pos = {"x": x, "y": 0}
        self.shape = self.piece[num_rotations]
        print(3)

        while not self.check_collision(self.shape, self.current_pos):
            self.current_pos["y"] += 1

        overflow = self.truncate(self.shape, self.current_pos)
        if overflow:
            self.gameover = True

        self.grid = self.store(self.shape, self.current_pos)

        lines_cleared, self.grid = self.check_cleared_rows()
        self.cleared_lines += lines_cleared
        if self.gameover:
            self.reward -= 2
        else:
            self.new_piece()
        
        self.drawShape(self.xp, self.yp)
        self.window.fill(self.bgColor)
        self.drawPoints()
        self.drawNext()
        self.drawGrid()
        self.drawDebug()

        return self.reward, self.gameover