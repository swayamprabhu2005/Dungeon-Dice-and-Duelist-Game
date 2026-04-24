import collections
import heapq

def get_neighbors(maze, r, c):
    rows = len(maze)
    cols = len(maze[0])
    neighbors = []
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0:
            neighbors.append((nr, nc))
    return neighbors

def a_star(maze, start, end):
    """
    Find shortest path from start to end using A* algorithm.
    Returns list of coordinates from start (not including start) to end.
    """
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    queue = [(0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while queue:
        _, current = heapq.heappop(queue)
        
        if current == end:
            break
            
        for nxt in get_neighbors(maze, current[0], current[1]):
            new_cost = cost_so_far[current] + 1
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                priority = new_cost + heuristic(end, nxt)
                heapq.heappush(queue, (priority, nxt))
                came_from[nxt] = current
                
    # Reconstruct path
    path = []
    curr = end
    if curr not in came_from:
        return [] # No path found
    
    while curr != start:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path

def bfs_reachable_exact(maze, start, distance):
    """
    Breadth First Search (BFS) to highlight reachable tiles.
    Constraint Satisfaction: Prevent walking through walls (checked by get_neighbors)
    Returns: Dict mapping {target_node: path_to_target} 
    """
    if distance == 0:
        return {start: []}
        
    queue = collections.deque([(start, [])])
    exact_paths = {}
    
    while queue:
        curr, path = queue.popleft()
        
        if len(path) == distance:
            if curr not in exact_paths:
                exact_paths[curr] = path
            continue
            
        for nxt in get_neighbors(maze, curr[0], curr[1]):
            # Avoid immediate backtracking
            if len(path) > 0 and nxt == path[-1]:
                continue
            # Optionally avoid crossing own path in single move to prevent logic loops
            if nxt not in path and nxt != start:
                queue.append((nxt, path + [nxt]))
                
    return exact_paths
