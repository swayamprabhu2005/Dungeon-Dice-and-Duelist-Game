import random

def generate_maze_dfs(rows, cols):
    """
    Depth First Search (DFS)
    Use: Generate a new random maze every game
    """
    g = [[1]*cols for _ in range(rows)]
    sr, sc = 1, 1
    g[sr][sc] = 0
    stack = [(sr, sc)]
    D = [(0, -2), (0, 2), (-2, 0), (2, 0)]
    
    while stack:
        r, c = stack[-1]
        random.shuffle(D)
        moved = False
        for dr, dc in D:
            nr, nc = r + dr, c + dc
            if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and g[nr][nc] == 1:
                g[r + dr//2][c + dc//2] = 0
                g[nr][nc] = 0
                stack.append((nr, nc))
                moved = True
                break
        if not moved:
            stack.pop()
            
    er, ec = rows - 2, cols - 2
    g[er][ec] = 0
    if g[er - 1][ec] == 1 and g[er][ec - 1] == 1:
        g[er - 1][ec] = 0
        
    return g, (sr, sc), (er, ec)