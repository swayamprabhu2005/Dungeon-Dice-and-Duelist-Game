# movement/bfs.py

from collections import deque


def get_neighbors(grid, row, col):
    cell = grid.get_cell(row, col)
    neighbors = []

    if not cell.walls["top"]:
        neighbors.append((row - 1, col))

    if not cell.walls["bottom"]:
        neighbors.append((row + 1, col))

    if not cell.walls["left"]:
        neighbors.append((row, col - 1))

    if not cell.walls["right"]:
        neighbors.append((row, col + 1))

    return neighbors


def bfs_reachable(grid, start, max_steps):
    """
    Returns all reachable cells within max_steps
    """
    queue = deque()
    queue.append((start, 0))

    visited = set()
    visited.add(start)

    reachable = []

    while queue:
        (row, col), steps = queue.popleft()

        if steps <= max_steps:
            reachable.append((row, col))

        if steps == max_steps:
            continue

        for nr, nc in get_neighbors(grid, row, col):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append(((nr, nc), steps + 1))

    return reachable