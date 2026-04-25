from collections import deque
from maze_game.maze.a_star_solver import grid_nb

def bfs_reachable_tiles(grid, start, max_steps):
    """
    Breadth First Search (BFS)
    Use: Find all reachable tiles within dice steps.
    Returns a dictionary mapping (row, col) -> shortest distance from start.
    """
    queue = deque([(start, 0)])
    visited = {start: 0}
    
    while queue:
        cur, steps = queue.popleft()
        if steps >= max_steps:
            continue
            
        for nb in grid_nb(grid, *cur):
            if nb not in visited:
                visited[nb] = steps + 1
                queue.append((nb, steps + 1))
                
    return visited