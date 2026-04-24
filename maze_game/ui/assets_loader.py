# ui/assets_loader.py

import pygame
import os
from pathlib import Path


def load_images(cell_size=25):
    # Resolve from project root so running `python -m maze_game` works.
    # Expected: <repo_root>/assets/images/...
    base_path = Path(__file__).resolve().parents[2] / "assets" / "images"
    assets = {}

    # 🎲 Dice (fixed size)
    for i in range(1, 7):
        img = pygame.image.load(
            str(base_path / "dice" / f"dice_{i}.png")
        ).convert_alpha()

        assets[f"dice_{i}"] = pygame.transform.scale(img, (80, 80))

    # 🟢 Player (small dot)
    player_img = pygame.image.load(
        str(base_path / "maze" / "player_dot.png")
    ).convert_alpha()

    assets["player"] = pygame.transform.scale(player_img, (16, 16))

    # 🟡 Goal
    goal_img = pygame.image.load(
        str(base_path / "maze" / "Goal.png")
    ).convert_alpha()

    assets["goal"] = pygame.transform.scale(goal_img, (18, 18))

    # 🎨 Background (FIT SCREEN)
    bg = pygame.image.load(
        str(base_path / "maze" / "background.png")
    ).convert()

    assets["background"] = pygame.transform.scale(bg, (800, 700))

    # ⬆️ Arrows (UI buttons)
    for direction in ["up", "down", "left", "right"]:
        img = pygame.image.load(
            str(base_path / "maze" / f"arrow_{direction}.png")
        ).convert_alpha()

        assets[f"arrow_{direction}"] = pygame.transform.scale(img, (40, 40))

    return assets