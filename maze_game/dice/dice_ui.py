# dice/dice_ui.py

import pygame
import time
from maze_game.dice.dice_logic import Dice


class DiceUI:
    def __init__(self, assets):
        self.dice = Dice()
        self.rolling = False
        self.roll_start_time = 0
        self.roll_duration = 1.5  # seconds

        # Load dice images
        self.images = {
            1: assets["dice_1"],
            2: assets["dice_2"],
            3: assets["dice_3"],
            4: assets["dice_4"],
            5: assets["dice_5"],
            6: assets["dice_6"],
        }

        self.current_value = None

        # Dice button area (adjust based on your UI)
        self.rect = pygame.Rect(350, 500, 100, 100)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos) and not self.rolling:
            self.rolling = True
            self.roll_start_time = time.time()
            self.current_value = None

    def update(self):
        if self.rolling:
            elapsed = time.time() - self.roll_start_time

            if elapsed >= self.roll_duration:
                self.current_value = self.dice.roll()
                self.rolling = False

    def draw(self, screen):
        # During rolling → show random flicker effect
        if self.rolling:
            fake_value = pygame.time.get_ticks() % 6 + 1
            image = self.images[fake_value]

        else:
            if self.current_value:
                image = self.images[self.current_value]
            else:
                image = self.images[1]  # default

        screen.blit(image, self.rect.topleft)

    def get_value(self):
        return self.current_value