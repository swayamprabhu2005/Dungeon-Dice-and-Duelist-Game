# for movement
def hill_climbing_movement(enemy_x, player_x, enemy_speed):
    """
    Hill Climbing
    Use: Enemy combat movement (Move toward player to maximize proximity/damage)
    """
    current_dist = abs(player_x - enemy_x)

    candidates = [
        enemy_x - enemy_speed,
        enemy_x,
        enemy_x + enemy_speed
    ]

    best_pos = enemy_x
    best_score = current_dist

    for pos in candidates:
        score = abs(player_x - pos)

        if score < best_score:
            best_score = score
            best_pos = pos

    movement = best_pos - enemy_x
    
    if movement > 0:
        facing = 1
    elif movement < 0:
        facing = -1
    else:
        facing = 1 if enemy_x < player_x else -1

    return movement, facing

# for resolving attacks
def forward_chaining_combat(attacker_rect, defender_rect, attacker_weapon_dmg):
    """
    Forward Chaining & Rule-Based System
    Use: Combat logic (Collision -> damage -> knockback -> check HP)
    Rules:
    R1: IF collision == True THEN apply damage
    R2: IF apply damage THEN apply knockback
    """
    collision = attacker_rect.colliderect(defender_rect)
    knockback_dir = 0
    damage_dealt = 0
    is_hit = False
    
    if collision: # R1
        damage_dealt = attacker_weapon_dmg
        is_hit = True
        
        # R2 (Forward Chaining: Knockback depends on collision relative position)
        if attacker_rect.centerx < defender_rect.centerx:
            knockback_dir = 1
        else:
            knockback_dir = -1
            
    return is_hit, damage_dealt, knockback_dir
