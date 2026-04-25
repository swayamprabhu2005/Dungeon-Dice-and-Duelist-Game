# maze_game/core/combat_ai.py

def hill_climbing_movement(enemy_x, player_x, enemy_speed):
    """
    Hill Climbing
    Use: Enemy combat movement (Move toward player to maximize proximity/damage)
    """
    # Objective function: Minimize distance to player
    dist = abs(enemy_x - player_x)
    if dist < 5:
        return 0, 1 if enemy_x < player_x else -1 # Optimal state reached
        
    if enemy_x < player_x:
        return enemy_speed, 1 # Move right (facing right)
    else:
        return -enemy_speed, -1 # Move left (facing left)

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
