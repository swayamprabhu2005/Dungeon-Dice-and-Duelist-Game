import random

def generate_maze(rows, cols):
    """
    Generates a perfect maze using Depth First Search (DFS).
    Output: 2D array (1 = wall, 0 = path), start_pos, exit_pos
    """
    # Grid dimensions should be odd for proper wall/path generation
    if rows % 2 == 0: rows -= 1
    if cols % 2 == 0: cols -= 1
    
    maze = [[1 for _ in range(cols)] for _ in range(rows)]
    
    start_r, start_c = 1, 1
    maze[start_r][start_c] = 0
    
    stack = [(start_r, start_c)]
    directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
    
    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 < nr < rows - 1 and 0 < nc < cols - 1 and maze[nr][nc] == 1:
                neighbors.append((dr, dc))
                
        if neighbors:
            # Pick a random unvisited neighbor
            dr, dc = random.choice(neighbors)
            maze[r + dr][c + dc] = 0           # carve neighbor
            maze[r + dr // 2][c + dc // 2] = 0 # carve intermediate wall
            stack.append((r + dr, c + dc))
        else:
            stack.pop()
            
    # Set exit to bottom-rightmost available path
    exit_r, exit_c = rows - 2, cols - 2
    if maze[exit_r][exit_c] == 1:
        # Guarantee a connection if the specific tile was left as wall 
        maze[exit_r][exit_c] = 0
        maze[exit_r-1][exit_c] = 0
        maze[exit_r][exit_c-1] = 0
        
    return maze, (start_r, start_c), (exit_r, exit_c)
