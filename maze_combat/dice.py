import random
import pygame
from settings import *

class Dice:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 60, 60)
        self.value = 1
        self.rolling = False
        self.roll_timer = 0
        self.font = pygame.font.SysFont(None, 48)
        
    def start_roll(self):
        self.rolling = True
        self.roll_timer = 20 # frames to roll
        
    def update(self):
        if self.rolling:
            self.value = random.randint(1, 6)
            self.roll_timer -= 1
            if self.roll_timer <= 0:
                self.rolling = False
                
    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, width=3, border_radius=10)
        
        # Draw value
        text = self.font.render(str(self.value), True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)
