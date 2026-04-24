import pygame
import random
from settings import *
from maze import generate_maze
from pathfinding import a_star, bfs_reachable_exact
from dice import Dice
from combat import CombatSystem
from entities import Weapon

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state = STATE_MAZE
        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 24)
        
        self.player_weapon = Weapon("Sword", "MELEE", 25, 10)
        self.combat_system = CombatSystem(self.screen)
        
        self.reset_maze()
        
    def reset_maze(self):
        self.maze, self.start_pos, self.exit_pos = generate_maze(MAZE_ROWS, MAZE_COLS)
        self.player_pos = self.start_pos
        self.optimal_path = a_star(self.maze, self.start_pos, self.exit_pos)
        
        self.dice = Dice(WIDTH - 100, HEIGHT - 100)
        self.reachable_tiles = {}
        self.mode = "WAIT_ROLL" # WAIT_ROLL, ROLLING, WAIT_MOVE, MOVING
        self.moving_path = []
        
        self.enemy_spawned = False
        self.enemy_pos = None
        self.enemy_weapon = None
        
    def trigger_enemy_spawn(self):
        if self.enemy_spawned: return
        
        if self.player_pos in self.optimal_path:
            idx = self.optimal_path.index(self.player_pos)
            spawn_idx = min(len(self.optimal_path)-1, idx + 3)
            self.enemy_pos = self.optimal_path[spawn_idx]
            self.enemy_spawned = True
            
            types = [("Energy Gun", "RANGED", 10, 5), ("Heavy Sword", "MELEE", 25, 15)]
            w_opt = random.choice(types)
            self.enemy_weapon = Weapon(w_opt[0], w_opt[1], w_opt[2], w_opt[3])
            
    def update(self):
        if self.state == STATE_MAZE:
            self.dice.update()
            
            if self.mode == "WAIT_ROLL":
                pass
            elif self.mode == "ROLLING":
                if not self.dice.rolling:
                    self.reachable_tiles = bfs_reachable_exact(self.maze, self.player_pos, self.dice.value)
                    if not self.reachable_tiles:
                        # No valid path of exactly dice roll length
                        self.mode = "WAIT_ROLL"
                    else:
                        self.mode = "WAIT_MOVE"
            elif self.mode == "MOVING":
                if len(self.moving_path) > 0:
                    self.player_pos = self.moving_path.pop(0)
                    pygame.time.delay(100)
                else:
                    self.mode = "WAIT_ROLL"
                    
                    if self.player_pos == self.exit_pos:
                        self.state = STATE_WIN
                        return
                        
                    self.trigger_enemy_spawn()
                    
                    if self.player_pos == self.enemy_pos:
                        self.state = STATE_COMBAT
                        self.combat_system.setup_match(self.player_weapon, self.enemy_weapon)
                        
        elif self.state == STATE_COMBAT:
            res = self.combat_system.update()
            if res == "PLAYER_DEAD":
                self.state = STATE_GAMEOVER
            elif res == "ENEMY_DEAD":
                self.state = STATE_MAZE
                self.enemy_spawned = False
                self.enemy_pos = None
                # Take enemy weapon
                self.player_weapon = self.enemy_weapon 
                self.mode = "WAIT_ROLL"

    def handle_event(self, event):
        if self.state == STATE_MAZE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.mode == "WAIT_ROLL":
                    self.dice.start_roll()
                    self.mode = "ROLLING"
                    
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.mode == "WAIT_MOVE":
                    mx, my = pygame.mouse.get_pos()
                    c = mx // TILE_SIZE
                    r = my // TILE_SIZE
                    if (r, c) in self.reachable_tiles:
                        self.moving_path = self.reachable_tiles[(r, c)]
                        self.reachable_tiles = {}
                        self.mode = "MOVING"
                        
        elif self.state == STATE_GAMEOVER or self.state == STATE_WIN:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_maze()
                    self.state = STATE_MAZE
                    
    def draw_maze(self):
        self.screen.fill(BLACK)
        
        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS):
                rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if self.maze[r][c] == 1:
                    pygame.draw.rect(self.screen, GRAY, rect)
                else:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
                    
        exit_r, exit_c = self.exit_pos
        pygame.draw.rect(self.screen, GREEN, (exit_c*TILE_SIZE, exit_r*TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        for (rr, rc) in self.reachable_tiles.keys():
            s = pygame.Surface((TILE_SIZE, TILE_SIZE))
            s.set_alpha(128)
            s.fill(CYAN)
            self.screen.blit(s, (rc*TILE_SIZE, rr*TILE_SIZE))
            
        if self.enemy_spawned and self.enemy_pos:
            er, ec = self.enemy_pos
            pygame.draw.circle(self.screen, RED, (ec*TILE_SIZE + TILE_SIZE//2, er*TILE_SIZE + TILE_SIZE//2), TILE_SIZE//3)
            
        pr, pc = self.player_pos
        pygame.draw.circle(self.screen, BLUE, (pc*TILE_SIZE + TILE_SIZE//2, pr*TILE_SIZE + TILE_SIZE//2), TILE_SIZE//3)
        
        self.dice.draw(self.screen)
        
        w_text = self.small_font.render(f"Weapon: {self.player_weapon.name} ({self.player_weapon.type})", True, WHITE)
        self.screen.blit(w_text, (10, HEIGHT - 30))
        
        if self.mode == "WAIT_ROLL":
            msg = self.font.render("Press SPACE to Roll", True, WHITE)
        elif self.mode == "WAIT_MOVE":
            msg = self.font.render("Click a highlighted tile", True, CYAN)
        else:
            msg = None
            
        if msg:
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 10))

    def draw(self):
        if self.state == STATE_MAZE:
            self.draw_maze()
        elif self.state == STATE_COMBAT:
            self.screen.fill(BLACK)
            self.combat_system.draw()
        elif self.state == STATE_GAMEOVER:
            self.screen.fill(BLACK)
            msg = self.font.render("GAME OVER - Press R to Restart", True, RED)
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
        elif self.state == STATE_WIN:
            self.screen.fill(BLACK)
            msg = self.font.render("YOU WIN! - Exit Reached. Press R to Restart", True, GREEN)
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
