# inspired by 

from  shapes import *
import pygame
from pygame.locals import * # Imports all of the keys that control the game (W,A,S,D...)
import random
from datetime import datetime ## FOR PLAYER GAME
import gspread ## SPREADSHEETS
from time import time

version = "23-game"

### CUSTOMIZE ###
MOVE_SPEED = 80
ROTATE_SPEED = 100
FALL_SPEED = 270
#################

##############################    INICIALIZATION    ##############################
grid = []

width,height = 288,338
bgColor = (95,95,178)
boxColor = (110,130,212)
size = 15
spacing = 2

pygame.init()
window = pygame.display.set_mode((width, height), pygame.SRCALPHA)
pygame.display.set_caption("Tetris game")
clock = pygame.time.Clock()

font = pygame.font.SysFont('confortaa', 32)

def createGrid(xg,yg):
    global grid
    for y in range(yg):
        grid.append([])
        for _ in range(xg):
            grid[y].append(0)

#############################################################################
        
##############################    MAIN    ##############################
def drawGrid(grid):    # for every element in the list, it creates a box with the 'size'
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            color = tetrominos_colors[grid[y][x]] # chooses the color with using the number of the grid block
            x_grid, y_grid = (size + spacing) * x, (size + spacing) * y # defines the positions of the grid blocks
            pygame.draw.rect(window, color, (x_grid, y_grid, size, size)) #Rect((left, top), (width, height)) 

def printGrid(grid): # prints the grid line
    for line in grid:
        print(line)

def clearLines(grid): # looks at every line in the gridand, if every space is occupied, it clears the line anc creates a new one
    linesCleared = 0
    for y in range(len(grid)):
        if not 0 in grid[y]:
            for yReplace in range(y, 0, -1): # start:y end:0 step:-1
                grid[yReplace] = grid[yReplace-1]
            grid[0] = [0] * len(grid[0]) # defines first line to be clear because of a bug where pieces stretch
            stats["linesCleared"] += 1 ## STAT
            linesCleared += 1
            
    return grid, linesCleared

def scoring(linesCleared, points, comboCount, level):
    actionPoints = 0
    if linesCleared > 0:
        comboCount += 1
        match linesCleared:
            case 1: # Single
                actionPoints += 100*level
                stats["pointsHistory"].append("1LINE") ## STAT
            case 2: # Double
                stats["pointsHistory"].append("2LINES") ## STAT
                actionPoints += 200*level
            case 3: # Triple
                stats["pointsHistory"].append("3LINES") ## STAT
                actionPoints += 400*level
            case 4: # Tetris
                stats["pointsHistory"].append("4LINES") ## STAT
                actionPoints += 800*level
        if comboCount > 1:
            actionPoints *= 1.5
    else:
        comboCount = 1

    return points+actionPoints

def newShape():
    shapeNum = random.randint(0, len(tetrominosStr)-1)
    shape = tetrominos[shapeNum]
    shapeChar = tetrominosStr[shapeNum]
    
    return shape, xg//2, 0, shapeChar

def drawPoints(points,font):
    superf_text = font.render("Score", True, "white")
    superf_points = font.render(f'{int(points)}', True, "white")
    rect_text = superf_text.get_rect()
    rect_points = superf_points.get_rect()
    rect_text.centerx = 228
    rect_points.centerx = 228
    rect_points.centery = 45
    pygame.draw.rect(window, boxColor, (178, 25, 100, 40), border_radius=5)
    window.blit(superf_text, rect_text)
    window.blit(superf_points, rect_points)
    
    
def drawNext(font, nextShape):
    superf_text = font.render("Next", True, "white")
    
    rect_text = superf_text.get_rect()
    rect_text.centerx = 228
    rect_text.centery = 95
    pygame.draw.rect(window, boxColor, (178, 110, 100, 80), border_radius=5)
    drawNextShape(nextShape, 0, 200, 115 + spacing)
    window.blit(superf_text, rect_text)

def drawPaused():
    superf_text = font.render("Paused", True, "black")
    rect_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    rect_surface.fill((255, 255, 255, 100))
    rect_text = superf_text.get_rect()
    rect_text.center = width//2, height//2
    window.blit(rect_surface, (0, 0))
    window.blit(superf_text, rect_text)

def drawDebug():
    superf_text = font.render(f"{clock.get_fps():.0f}", True, "black")
    rect_text = superf_text.get_rect()
    rect_text.centerx = 228
    rect_text.centery = 300
    window.blit(superf_text, rect_text)

def drawGameOver():
    superf_text = font.render("GAME OVER", True, "black")
    rect_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    rect_surface.fill((255, 80, 80, 100))
    rect_text = superf_text.get_rect()
    rect_text.center = width//2, height//2
    window.blit(rect_surface, (0, 0))
    window.blit(superf_text, rect_text)

def replacePos(grid,x,y,val):
    grid[y][x] = val

def drawShape(grid,shape,rotation,x,y):
    shape = shape [rotation]
    
    xb = -1
    yb = -1
    for shapeY in shape:
        yb += 1
        xb = -1
        for shapePiece in shapeY:
            xb += 1
            if shapePiece != 0: # switch case is slower 13/5/24  https://www.andrewjmoodie.com/blog/2018/09-04-2018-matlab-speed-comparison-of-switch-case-and-if-then-statements-and-hard-code/#:~:text=It%20turns%20out%20that%20switch,then%20or%20case%2Dswitch%20statement.
                replacePos(grid,x+xb,y+yb,shapePiece)
    
def drawNextShape(shape,rotation,xs,ys):
    shape = shape [rotation]

    for y in range(len(shape)):
        for x in range(len(shape[y])):
            x_grid, y_grid = (size + spacing) * x + xs, (size + spacing) * y + ys # defines the positions of the grid blocks
            color = tetrominos_colors[shape[y][x]] # chooses the color with using the number of the grid block
            if not shape[y][x] == 0:
                pygame.draw.rect(window, color, (x_grid, y_grid, size, size)) #Rect((left, top), (width, height)) 
    
    
    # for shapeY in shape:
    #     for shapePiece in shapeY:
    #         if shapePiece != 0: # switch case is slower 13/5/24  https://www.andrewjmoodie.com/blog/2018/09-04-2018-matlab-speed-comparison-of-switch-case-and-if-then-statements-and-hard-code/#:~:text=It%20turns%20out%20that%20switch,then%20or%20case%2Dswitch%20statement.
    #             replacePos(grid,x+xb,y+yb,shapePiece)

def clearShape(grid,shape,rotation,x,y):
    shape = shape[rotation]
    
    yb = -1
    for shapeY in shape:
        yb += 1
        xb = -1
        for shapePiece in shapeY:
            xb += 1
            if shapePiece != 0:
                replacePos(grid,x+xb,y+yb,0)

def resetGame():
    for line in range(len(grid)):
        grid[line] = [0] * len(grid[0])
    points = 0
    xp,yp = xg//2, 0
    currentRotation = 0
    print("[DEBUG] RESET")
    gameOver = False

    return grid, xp, yp, points, currentRotation, gameOver

def collisionShape(grid,shape,rotation,x,y):
    shape = shape[rotation]

    yb = -1
    for shapeY in shape:
        yb += 1
        xb = -1
        for shapePiece in shapeY:
            xb += 1
            if shapePiece != 0:
                try:
                    if grid[y+yb][x+xb] != 0:
                        return True
                    if x+xb < 0:
                        return True
                except:
                    return True
    return False

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
    wks = sh.worksheet("PLAYERS")

    i=2
    while wks.get('A'+str(i))[0] != []: # while empty cell value
        i+=1

    stats_list = []
    for a in stats:
        stats_list.append(str(stats[a]))
        
    wks.update('A'+str(i), [stats_list])
    print("[DEBUG] SAVED STATS!")

###################################################################

xg, yg = 10, 20
createGrid(xg, yg)

executant = True
points = 0
level = 1
comboCount = 1
gameTime = time()
moveTime = 0
fallTime = 0
stats = {
    "version": version,
    "dateTime": "",
    "timePlayed": 0,
    "points": 0,
    "pointsHistory": [],
    "linesCleared": 0,
    "windowStats": {"gridSize": (xg, yg), "screenSize": (width,height)},
    "controlHistory": [],
    "pieceHistory": [],
}
movement = {"up": False, "left": False, "down": False, "right": False}
movementDelay = {"left": 0, "down": 0, "right": 0}

currentShape, xp, yp, shapeChar= newShape()
nextShape, xp, yp, nextShapeChar = newShape()
currentRotation = 0
changePiece = False
paused = False
gameOver = False

while executant:
    
    if paused or gameOver:
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    executant = False
            # general player movement
                if event.type == pygame.KEYDOWN: 
                    if event.key == pygame.K_p:
                        stats["controlHistory"] += "P" ## CONTROL STAT
                        paused = not paused
                    
                

    window.fill(bgColor)
    drawPoints(points,font)
    drawNext(font,nextShape)
    drawGrid(grid)
    # drawDebug()

    if not paused and not gameOver:
        fallTime += clock.get_rawtime()
        clock.tick()
 
        clearShape(grid, currentShape, currentRotation, xp, yp)
        
        if fallTime > FALL_SPEED:
            fallTime = 0
            yp += 1
            if collisionShape(grid, currentShape, currentRotation, xp,yp): # if the shape collides in the next 
                changePiece = True
                yp -= 1
                
        #############    MOVEMENT    #############
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                executant = False
        # general player movement
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    stats["controlHistory"] += "W" ## CONTROL STAT
                    # rotate_delay["up"] = 0
                    currentRotation += 1
                    if currentRotation > 3:
                        currentRotation = 0
                    while collisionShape(grid,currentShape,currentRotation,xp,yp):
                        currentRotation -= 1
                if event.key == pygame.K_r: ## RESET GAME DEBUG
                    grid, xp, yp, points, currentRotation, gameOver = resetGame()
                if event.key == pygame.K_SPACE:
                    stats["controlHistory"].append("SPACE") ## CONTROL STAT
                    while not collisionShape(grid,currentShape,currentRotation,xp,yp+1):
                        yp += 1
                        points += 2
                    changePiece = True
                if event.key == pygame.K_p:
                    stats["controlHistory"] += "P" ## CONTROL STAT
                    paused = not paused
                

        keys = pygame.key.get_pressed()

        # if keys[pygame.K_w] or keys[pygame.K_UP]:
        #     rotate_delay["up"] += clock.get_rawtime()

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            movementDelay["left"] += clock.get_rawtime()
            
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movementDelay["down"] += clock.get_rawtime()
            
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            movementDelay["right"] += clock.get_rawtime()

        # if rotate_delay["up"] > rotateSpeed:
        #     stats["controlHistory"] += "W" ## CONTROL STAT
        #     rotate_delay["up"] = 0
        #     currentRotation += 1
        #     if currentRotation > 3:
        #         currentRotation = 0
        #     while collisionShape(grid,currentShape,currentRotation,xp,yp):
        #         currentRotation -= 1

        for direction in movementDelay:
            if movementDelay[direction] > MOVE_SPEED:
                movement[direction] = True
                movementDelay[direction] = 0

                if movement['left']:
                    stats["controlHistory"] += "A" ## CONTROL STAT
                    xp -= 1
                    
                    if collisionShape(grid,currentShape,currentRotation,xp,yp):
                        xp += 1

                if movement['down']:
                    stats["controlHistory"] += "S" ## CONTROL STAT
                    yp += 1
                    points += 1
                    if collisionShape(grid,currentShape,currentRotation,xp,yp): # if the shape collides in the next
                        changePiece = True
                        yp -=1
                        points -= 1
                        
                
                if movement['right']:
                    stats["controlHistory"] += "D" ## CONTROL STAT
                    xp += 1
                    if collisionShape(grid,currentShape,currentRotation,xp,yp):
                        xp -= 1
                
                movement[direction] = False
        ########################################
        
        drawShape(grid, currentShape, currentRotation, xp, yp)

        if changePiece:
            for i in grid[0]:
                if i > 0:
                    stats["dateTime"] = datetime.now() ## STAT
                    stats["points"] = points ## STAT
                    stats["timePlayed"] = time() - gameTime ## STAT
                    uploadStats(stats)
                    print("[DEBUG] GAME OVER")
                    gameOver = True
                    
                    
            stats["pieceHistory"].append(shapeChar)
            currentShape, shapeChar = nextShape, nextShapeChar
            nextShape, xp, yp, nextShapeChar = newShape()
            grid, linesCleared = clearLines(grid)
            points = scoring(linesCleared, points, comboCount, level)
            changePiece = False
    elif paused:
        drawPaused()
    elif gameOver:
        drawGameOver()

    pygame.display.update()

pygame.quit()
quit()