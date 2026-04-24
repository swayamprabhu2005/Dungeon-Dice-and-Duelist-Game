# maze/dfs_generator.py

import random


def remove_walls(current, next_cell, direction):
    if direction == "top":
        current.walls["top"] = False
        next_cell.walls["bottom"] = False

    elif direction == "bottom":
        current.walls["bottom"] = False
        next_cell.walls["top"] = False

    elif direction == "left":
        current.walls["left"] = False
        next_cell.walls["right"] = False

    elif direction == "right":
        current.walls["right"] = False
        next_cell.walls["left"] = False


def generate_maze(grid):
    stack = []

    start = grid.get_cell(0, 0)
    start.visited = True
    stack.append(start)

    while stack:
        current = stack[-1]

        neighbors = grid.get_unvisited_neighbors(current)

        if neighbors:
            direction, next_cell = random.choice(neighbors)

            remove_walls(current, next_cell, direction)

            next_cell.visited = True
            stack.append(next_cell)

        else:
            stack.pop()

    return grid