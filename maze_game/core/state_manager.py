# core/state_manager.py

class GameState:
    MAZE = "maze"
    COMBAT = "combat"
    WIN = "win"
    LOSE = "lose"


class StateManager:
    def __init__(self):
        self.state = GameState.MAZE

    def set_state(self, new_state):
        self.state = new_state

    def get_state(self):
        return self.state