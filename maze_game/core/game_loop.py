# core/game_loop.py

import pygame

from maze_game.maze.grid import Grid
from maze_game.maze.dfs_generator import generate_maze
from maze_game.player.player import Player
from maze_game.ui.renderer import Renderer
from maze_game.ui.assets_loader import load_images
from maze_game.dice.dice_ui import DiceUI
from maze_game.movement.bfs import bfs_reachable
from maze_game.movement.constraints import filter_exact_steps


class Game:
    def __init__(self, config):
        pygame.init()

        self.config = config
        self.screen = pygame.display.set_mode(
            (config.WIDTH, config.HEIGHT)
        )
        pygame.display.set_caption("Maze Game")

        self.clock = pygame.time.Clock()
        
        self.assets = load_images(config.CELL_SIZE)

        # Create systems
        self.grid = Grid(config.ROWS, config.COLS)
        generate_maze(self.grid)

        self.player = Player(0, 0)
        self.goal = (config.ROWS - 1, config.COLS - 1)

        # ✅ PASS ASSETS TO RENDERER (IMPORTANT FIX)
        self.renderer = Renderer(self.screen, config.CELL_SIZE, self.assets)

        self.dice_ui = DiceUI(self.assets)

        self.running = True

        # Movement system
        self.current_moves = []

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    # -------------------------
    # INPUT HANDLING
    # -------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.dice_ui.handle_click(mouse_pos)

            elif event.type == pygame.KEYDOWN:
                self.handle_movement(event.key)

    # -------------------------
    # MOVEMENT
    # -------------------------
    def handle_movement(self, key):
        dice_value = self.dice_ui.get_value()

        if dice_value is None:
            return

        directions = {
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
        }

        if key in directions:
            direction = directions[key]

            # Move step-by-step
            for _ in range(dice_value):
                self.player.move(direction, self.grid)

            # Reset dice after movement
            self.dice_ui.current_value = None
            self.current_moves = []

    # -------------------------
    # UPDATE
    # -------------------------
    def update(self):
        self.dice_ui.update()

        # Compute possible moves (BFS + CSP)
        dice_value = self.dice_ui.get_value()

        if dice_value:
            start = self.player.get_position()
            reachable = bfs_reachable(self.grid, start, dice_value)
            self.current_moves = filter_exact_steps(start, reachable, dice_value)

    # -------------------------
    # RENDER
    # -------------------------
    def render(self):
        # Background (image if available, else color)
        if self.assets.get("background"):
            self.renderer.draw_background()
        else:
            self.screen.fill((10, 10, 10))

        # Maze
        self.renderer.draw_maze(self.grid)

        # Goal + Player
        self.renderer.draw_goal(self.goal)
        self.renderer.draw_player(self.player)

        # Dice UI
        self.dice_ui.draw(self.screen)