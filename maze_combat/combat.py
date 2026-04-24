import pygame
from settings import *
from entities import Stickman

class CombatSystem:
    def __init__(self, surface):
        self.surface = surface
        self.arena_rect = pygame.Rect(50, 100, WIDTH - 100, HEIGHT - 150)
        self.player = None
        self.enemy = None
        self.projectiles = []
        self.active = False
        
    def setup_match(self, p_weapon, e_weapon):
        self.player = Stickman(100, HEIGHT - 100, BLUE, is_player=True)
        self.player.weapon = p_weapon
        
        self.enemy = Stickman(WIDTH - 150, HEIGHT - 100, RED, is_player=False)
        self.enemy.weapon = e_weapon
        
        self.projectiles = []
        self.active = True
        
    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-PLAYER_SPEED_COMBAT)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(PLAYER_SPEED_COMBAT)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player.jump()
            
    def enemy_ai(self):
        """
        Hill climbing / simple goal-based logic.
        """
        if not self.enemy: return
        
        dx = self.player.rect.centerx - self.enemy.rect.centerx
        dy = self.player.rect.y - self.enemy.rect.y
        dist = abs(dx)
        
        if self.enemy.weapon.type == "MELEE":
            if dist > 35:
                if dx > 0: self.enemy.move(PLAYER_SPEED_COMBAT * 0.8)
                else: self.enemy.move(-PLAYER_SPEED_COMBAT * 0.8)
            else:
                self.enemy.attack(self.projectiles)
        else:
            if dist < 150:
                if dx > 0: self.enemy.move(-PLAYER_SPEED_COMBAT * 0.8)
                else: self.enemy.move(PLAYER_SPEED_COMBAT * 0.8)
            elif dist > 250:
                if dx > 0: self.enemy.move(PLAYER_SPEED_COMBAT * 0.8)
                else: self.enemy.move(-PLAYER_SPEED_COMBAT * 0.8)
            else:
                self.enemy.facing_right = (dx > 0)
                if abs(dy) < 50:
                    self.enemy.attack(self.projectiles)
                    
        # Jump obstacle/stuck
        if self.enemy.vx == 0 and dist > 50: 
            self.enemy.jump()
            
    def update(self):
        if not self.active: return "FIGHTING"
        
        self.handle_input()
        self.enemy_ai()
        
        self.player.update(self.arena_rect)
        self.enemy.update(self.arena_rect)
        
        # Player Attack
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            if self.player.attack(self.projectiles):
                if self.player.weapon.type == "MELEE":
                    hitbox = self.player.get_melee_rect()
                    if hitbox.colliderect(self.enemy.rect):
                        self.enemy.hp -= self.player.weapon.damage
                        self.enemy.vx = self.player.weapon.knockback if self.player.facing_right else -self.player.weapon.knockback
                        self.enemy.vy = -5
                        
        # Enemy Melee Attack Check
        if self.enemy.weapon.type == "MELEE" and self.enemy.attack_cooldown == 39:
            hitbox = self.enemy.get_melee_rect()
            if hitbox.colliderect(self.player.rect):
                self.player.hp -= self.enemy.weapon.damage
                self.player.vx = self.enemy.weapon.knockback if self.enemy.facing_right else -self.enemy.weapon.knockback
                self.player.vy = -5
                
        # Projectiles
        for p in self.projectiles[:]:
            p.update()
            if not self.arena_rect.colliderect(p.rect):
                self.projectiles.remove(p)
                continue
            
            if p.owner != self.player and p.rect.colliderect(self.player.rect):
                self.player.hp -= p.owner.weapon.damage
                self.player.vx = p.owner.weapon.knockback if p.vx > 0 else -p.owner.weapon.knockback
                self.projectiles.remove(p)
            elif p.owner != self.enemy and p.rect.colliderect(self.enemy.rect):
                self.enemy.hp -= p.owner.weapon.damage
                self.enemy.vx = p.owner.weapon.knockback if p.vx > 0 else -p.owner.weapon.knockback
                self.projectiles.remove(p)
                
        if self.player.hp <= 0:
            return "PLAYER_DEAD"
        if self.enemy.hp <= 0:
            return "ENEMY_DEAD"
            
        return "FIGHTING"
        
    def draw(self):
        pygame.draw.rect(self.surface, DARK_GRAY, self.arena_rect)
        pygame.draw.line(self.surface, WHITE, (self.arena_rect.left, self.arena_rect.bottom), (self.arena_rect.right, self.arena_rect.bottom), 5)
        
        self.player.draw(self.surface)
        self.enemy.draw(self.surface)
        
        for p in self.projectiles:
            p.draw(self.surface)
            
        font = pygame.font.SysFont(None, 36)
        text = font.render(f"Combat! Space: Attack, Arrows/WASD: Move, Up: Jump", True, WHITE)
        self.surface.blit(text, (50, 50))
