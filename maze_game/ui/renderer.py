# ui/renderer.py

import pygame


class Renderer:
    def __init__(self, screen, cell_size, assets=None):
        self.screen = screen
        self.cell_size = cell_size
        self.assets = assets or {}

        # 🎨 Styling
        self.wall_color = (255, 140, 80)
        self.glow_color = (255, 100, 60)

        self.wall_thickness = 3
        self.glow_thickness = 6

    # -------------------------
    # MAIN DRAW FUNCTIONS
    # -------------------------

    def draw_maze(self, grid):
        for row in grid.cells:
            for cell in row:
                self.draw_cell(cell)

    def draw_background(self):
        if "background" in self.assets:
            self.screen.blit(self.assets["background"], (0, 0))

    # -------------------------
    # CELL DRAWING (WALLS)
    # -------------------------

    def draw_cell(self, cell):
        x = cell.col * self.cell_size
        y = cell.row * self.cell_size

        # Top wall
        if cell.walls["top"]:
            self.draw_glow_line((x, y), (x + self.cell_size, y))

        # Right wall
        if cell.walls["right"]:
            self.draw_glow_line(
                (x + self.cell_size, y),
                (x + self.cell_size, y + self.cell_size),
            )

        # Bottom wall
        if cell.walls["bottom"]:
            self.draw_glow_line(
                (x, y + self.cell_size),
                (x + self.cell_size, y + self.cell_size),
            )

        # Left wall
        if cell.walls["left"]:
            self.draw_glow_line((x, y), (x, y + self.cell_size))

    def draw_glow_line(self, start, end):
        # Glow layer (thicker)
        pygame.draw.line(
            self.screen,
            self.glow_color,
            start,
            end,
            self.glow_thickness,
        )

        # Main line (on top)
        pygame.draw.line(
            self.screen,
            self.wall_color,
            start,
            end,
            self.wall_thickness,
        )

    # -------------------------
    # PLAYER
    # -------------------------

    def draw_player(self, player):
        px = player.col * self.cell_size + self.cell_size // 2
        py = player.row * self.cell_size + self.cell_size // 2

        if self.assets.get("player"):
            rect = self.assets["player"].get_rect(center=(px, py))
            self.screen.blit(self.assets["player"], rect)
        else:
            pygame.draw.circle(self.screen, (0, 255, 0), (px, py), 6)

    # -------------------------
    # GOAL
    # -------------------------

    def draw_goal(self, goal_pos):
        row, col = goal_pos

        gx = col * self.cell_size + self.cell_size // 2
        gy = row * self.cell_size + self.cell_size // 2

        if self.assets.get("goal"):
            rect = self.assets["goal"].get_rect(center=(gx, gy))
            self.screen.blit(self.assets["goal"], rect)
        else:
            pygame.draw.circle(self.screen, (255, 255, 0), (gx, gy), 6)