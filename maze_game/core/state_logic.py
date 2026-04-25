# maze_game/core/state_logic.py

# Game States
S_MENU, S_MODE, S_MAZE, S_COMBAT, S_OVER, S_WIN = "MENU", "MODE", "MAZE", "COMBAT", "OVER", "WIN"

def evaluate_game_state(current_state, player_hp, enemy_hp, player_pos, exit_pos, enemy_triggered):
    """
    Propositional Logic (again)
    Use: Game states (Maze -> Combat, Combat -> Maze, Win / Lose)
    P: Player HP <= 0
    Q: Player reached exit
    R: Enemy Triggered
    S: Enemy HP <= 0
    """
    if player_hp <= 0:
        return S_OVER
        
    if current_state == S_MAZE:
        if player_pos == exit_pos:
            return S_WIN
        if enemy_triggered:
            return S_COMBAT
            
    elif current_state == S_COMBAT:
        if enemy_hp <= 0:
            return S_MAZE
            
    return current_state
