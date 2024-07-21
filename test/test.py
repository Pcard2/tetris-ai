import random

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
bag = list(range(len(pieces)))
random.shuffle(bag)
ind = bag.pop()
piece = [row[:] for row in pieces[ind]]

print(piece)

curr_piece = [row[:] for row in piece]

print(curr_piece)

piece = [row[:] for row in curr_piece]

print(piece)