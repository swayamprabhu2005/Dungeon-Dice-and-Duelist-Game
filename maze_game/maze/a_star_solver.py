import heapq

def grid_nb(g, r, c):
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(g) and 0 <= nc < len(g[0]) and g[nr][nc] == 0:
            yield (nr, nc)

def astar_solver(g, start, goal):
    """
    A* Algorithm
    Use: Find optimal path from player -> exit, and for enemy positioning.
    """
    def h(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    q = [(h(start, goal), 0, start)]
    came = {start: None}
    cost = {start: 0}
    
    while q:
        _, c, cur = heapq.heappop(q)
        if cur == goal:
            path = []
            n = cur
            while n != start:
                path.append(n)
                n = came[n]
            return path[::-1]
            
        for nb in grid_nb(g, *cur):
            nc2 = c + 1
            if nb not in cost or nc2 < cost[nb]:
                cost[nb] = nc2
                came[nb] = cur
                heapq.heappush(q, (nc2 + h(nb, goal), nc2, nb))
                
    return []
