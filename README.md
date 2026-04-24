# Stickman Maze Combat

A 2D game combining maze exploration with action-packed 1v1 combat, built using Python and Pygame.

## Features
- **Maze Exploration**: Roll the dice to move through procedurally generated mazes using A* pathfinding to reach the goal.
- **Combat Mechanics**: Engage in 1v1 battles with enemy stickmen. Utilize different weapons (Sword, Energy Gun, War Axe, Energy Lance, Spear) and particle-based visual effects.
- **Dynamic Difficulties**: Choose between Easy, Medium, and Hard, which alter HP, enemy damage, and speed.

## Dependencies

Before running the game, you need to install the required libraries:

```bash
pip install pygame opencv-python numpy
```

## How to Run

Execute the main script from your terminal:

```bash
python finish_main.py
```

## Controls

### General
- **F11**: Toggle Fullscreen

### Maze Phase
- **SPACE / Click Dice**: Roll the dice to get movement steps.
- **Arrow Keys**: Move your character (one step per key-press, consumes dice steps).

### Combat Phase
- **A / D or Left / Right Arrows**: Move Left / Right
- **W or Up Arrow**: Jump
- **SPACE**: Attack

### End Screens
- **R**: Restart
- **Q**: Quit
