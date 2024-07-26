def createGrid(xg,yg):
  grid = []
  for y in range(yg):
      grid.append([])
      for _ in range(xg):
          grid[y].append(0)
  return grid

grid = createGrid(10,20)

for x in grid:
    if 0 not in grid[x]:
        print("a")