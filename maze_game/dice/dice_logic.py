# dice/dice_logic.py

import random


class Dice:
    def __init__(self):
        self.value = None

    def roll(self):
        self.value = random.randint(1, 6)
        return self.value

    def get_value(self):
        return self.value