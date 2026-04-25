# maze_game/core/spawn_logic.py

def evaluate_propositional_logic(player_on_path, path_progress_percent):
    """
    Propositional Logic
    Use: Trigger enemy spawn based on formal rules.
    P = Player is on the optimal A* path
    Q = Player has progressed > 20% along the path
    SPAWN = P AND Q
    """
    return player_on_path and (path_progress_percent > 0.20)

def spawn_goal_tree(grid, player_pos, exit_pos, astar_path, current_step_count):
    """
    Goal Tree (Simple Planning)
    Use: Structure spawn logic: Detect progress -> confirm correct path -> spawn
    """
    if not astar_path:
        return False, None
        
    path_len = len(astar_path)
    progress_percent = current_step_count / path_len if path_len > 0 else 0
    
    player_on_path = player_pos in astar_path
    
    # Evaluate Propositional Logic
    should_spawn = evaluate_propositional_logic(player_on_path, progress_percent)
    
    spawn_pos = None
    if should_spawn:
        # A* Algorithm (reuse) for Smart Enemy Positioning
        # Pick tile ahead of player on A* path (+3 steps)
        try:
            player_idx = astar_path.index(player_pos)
            spawn_idx = min(player_idx + 3, path_len - 1)
            spawn_pos = astar_path[spawn_idx]
        except ValueError:
            spawn_pos = astar_path[-1] # Fallback
            
    return should_spawn, spawn_pos
