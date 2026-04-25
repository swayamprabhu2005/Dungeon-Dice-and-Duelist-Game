def csp_valid_moves(reachable_tiles_dict, exact_steps, exit_pos):
    """
    Constraint Satisfaction (CSP)
    Use: Enforce movement rules (Dice value = exact steps, only valid paths).
    """
    valid_tiles = []
    for tile, steps in reachable_tiles_dict.items():
        # Constraint: Dice value must equal exact steps, UNLESS it's the exit tile!
        if steps == exact_steps or (tile == exit_pos and steps <= exact_steps):
            valid_tiles.append(tile)
    return valid_tiles