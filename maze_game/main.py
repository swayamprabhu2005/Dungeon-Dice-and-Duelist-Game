# main.py

from maze_game.core.game_loop import Game
from maze_game.config import Config


def main():
    game = Game(Config)
    game.run()


if __name__ == "__main__":
    main()