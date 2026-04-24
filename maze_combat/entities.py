import pygame
import math
from settings import *

class Weapon:
    def __init__(self, name, type, damage, knockback):
        self.name = name
        self.type = type # "MELEE" or "RANGED"
        self.damage = damage
        self.knockback = knockback
        
class Projectile:
    def __init__(self, x, y, vx, owner):
        self.rect = pygame.Rect(x, y, 10, 5)
        self.vx = vx
        self.owner = owner
        
    def update(self):
        self.rect.x += self.vx
        
    def draw(self, surface):
        pygame.draw.rect(surface, CYAN, self.rect)

class Stickman:
    def __init__(self, x, y, color, is_player=False):
        self.rect = pygame.Rect(x, y, 20, 50)
        self.color = color
        self.is_player = is_player
        self.hp = 100
        self.max_hp = 100
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        
        self.weapon = None # Assigned in setup
            
        self.attack_cooldown = 0
        self.facing_right = True if self.is_player else False

    def update(self, arena_rect):
        # Physics
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
            
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # Apply friction
        self.vx *= FRICTION
        if abs(self.vx) < 0.5:
            self.vx = 0
            
        # Collision with floor
        if self.rect.bottom >= arena_rect.bottom:
            self.rect.bottom = arena_rect.bottom
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False
            
        # Collision with walls
        if self.rect.left < arena_rect.left:
            self.rect.left = arena_rect.left
            self.vx = 0
        if self.rect.right > arena_rect.right:
            self.rect.right = arena_rect.right
            self.vx = 0
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_FORCE
            
    def move(self, dir_x):
        self.vx += dir_x
        if dir_x > 0:
            self.facing_right = True
        elif dir_x < 0:
            self.facing_right = False
            
    def draw(self, surface):
        # Stickman rendering
        cx = self.rect.centerx
        cy = self.rect.y + 10
        # Head
        pygame.draw.circle(surface, self.color, (cx, cy), 10, 2)
        # Body
        pygame.draw.line(surface, self.color, (cx, cy+10), (cx, self.rect.y + 35), 2)
        # Legs
        pygame.draw.line(surface, self.color, (cx, self.rect.y + 35), (self.rect.left, self.rect.bottom), 2)
        pygame.draw.line(surface, self.color, (cx, self.rect.y + 35), (self.rect.right, self.rect.bottom), 2)
        
        # Arms & Weapon
        arm_end_x = self.rect.right + 10 if self.facing_right else self.rect.left - 10
        pygame.draw.line(surface, self.color, (cx, self.rect.y + 20), (arm_end_x, self.rect.y + 20), 2)
        
        if self.weapon.type == "MELEE":
            pygame.draw.line(surface, GRAY, (arm_end_x, self.rect.y + 20), (arm_end_x, self.rect.y), 4)
        else:
            pygame.draw.line(surface, RED, (arm_end_x, self.rect.y + 20), (arm_end_x + (10 if self.facing_right else -10), self.rect.y + 20), 4)
            
        # Draw HP bar
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 15, self.rect.width, 5))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 15, self.rect.width * hp_ratio, 5))

    def attack(self, projectiles):
        if self.attack_cooldown <= 0:
            self.attack_cooldown = 40
            if self.weapon.type == "RANGED":
                vx = 10 if self.facing_right else -10
                arm_end_x = self.rect.right + 10 if self.facing_right else self.rect.left - 10
                p = Projectile(arm_end_x, self.rect.y + 20, vx, self)
                projectiles.append(p)
            return True
        return False
        
    def get_melee_rect(self):
        """Hitbox for melee attack"""
        if self.facing_right:
            return pygame.Rect(self.rect.right, self.rect.y, 30, self.rect.height)
        else:
            return pygame.Rect(self.rect.left - 30, self.rect.y, 30, self.rect.height)
