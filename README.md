# 🗡 Stickman Maze Combat

A 2D game combining procedurally generated maze exploration with action-packed 1v1 stickman combat, built in Python + Pygame. Every system is powered by a named AI/CS algorithm.

---

## 🚀 Quick Start

```bash
pip install pygame opencv-python numpy
python finish_main.py
```

---

## 🎮 Controls

| Phase | Key | Action |
|---|---|---|
| **Maze** | `SPACE` / click dice | Roll the dice |
| **Maze** | Arrow Keys | Move one step (consumes dice steps) |
| **Combat** | `A` / `D` | Move left / right |
| **Combat** | `W` | Jump |
| **Combat** | `SPACE` | Attack |
| **Any** | `F11` | Toggle fullscreen |
| **End screen** | `R` | Restart |
| **End screen** | `Q` | Quit |

---

## 🤖 AI Algorithms

| # | Algorithm | Used For | Module |
|---|---|---|---|
| 1 | **DFS** (Depth-First Search) | Generate a unique random maze every game | `maze_game/maze/dfs_generator.py` |
| 2 | **BFS** (Breadth-First Search) | Find all tiles reachable within your dice roll | `maze_game/movement/bfs.py` |
| 3 | **CSP** (Constraint Satisfaction) | Enforce movement rules — exact steps, no wall crossing | `maze_game/movement/constraints.py` |
| 4 | **A\*** | Compute the optimal path from start → exit once per maze | `maze_game/maze/a_star_solver.py` |
| 5 | **A\* (reuse)** | Pick smart enemy spawn tile (+3 steps ahead on A\* path) | `maze_game/core/spawn_logic.py` |
| 6 | **Propositional Logic** | Trigger enemy spawn when player follows A\* path > 20% | `maze_game/core/spawn_logic.py` |
| 7 | **Goal Tree** | Structured spawn planning: detect progress → confirm path → spawn | `maze_game/core/spawn_logic.py` |
| 8 | **Rule-Based System** | Combat: hit → damage → knockback → check HP | `maze_game/core/combat_ai.py` |
| 9 | **Forward Chaining** | Real-time chain: collision → `is_hit` → `damage_dealt` → `knockback_dir` | `maze_game/core/combat_ai.py` |
| 10 | **Hill Climbing** | Enemy moves toward player to minimise distance (objective function) | `maze_game/core/combat_ai.py` |
| 11 | **Propositional Logic** | Game state machine: Maze↔Combat, Win, Lose | `maze_game/core/state_logic.py` |

---

## 📁 Project Structure

```
D3 Game/
├── finish_main.py              # Single entry point — main game
│
├── maze_game/                  # Algorithm & logic modules
│   ├── maze/
│   │   ├── dfs_generator.py    # DFS maze generation
│   │   └── a_star_solver.py    # A* pathfinding
│   ├── movement/
│   │   ├── bfs.py              # BFS reachable tiles
│   │   └── constraints.py      # CSP movement rules
│   ├── core/
│   │   ├── spawn_logic.py      # Propositional Logic + Goal Tree + A* spawn
│   │   ├── combat_ai.py        # Hill Climbing + Forward Chaining + Rule-Based
│   │   └── state_logic.py      # Propositional Logic game states
│   └── assets/
│       ├── images/
│       │   ├── dice/           # dice_1.png … dice_6.png
│       │   └── maze/           # background.png, player_dot.png, Goal.png
│       └── videos/
│           └── dice_roll.mp4   # Dice roll animation
│
└── maze_combat/                # Combat runtime assets
    ├── backgrounds/            # 1.jpeg … 6.jpeg (random arena BGs)
    └── Weapons/                # Weapon sprite PNGs
        ├── Sword.png
        ├── War Axe.png
        ├── Energy Gun.png
        ├── Rocket Launcher.png
        └── Spear.png
```

---

## ⚙️ Difficulty Modes

| Mode | Player HP | Enemy HP | Damage Mult | Enemy Speed |
|---|---|---|---|---|
| Easy | 150 | 80 | ×0.7 | 2.0 |
| Medium | 120 | 120 | ×1.0 | 2.8 |
| Hard | 90 | 160 | ×1.35 | 3.8 |

---

## 🛠 Dependencies

```
pygame
opencv-python   # optional — enables dice roll video animation
numpy           # required by opencv-python
```

Install all at once:

```bash
pip install pygame opencv-python numpy
```

> **Note:** If `opencv-python` / `numpy` are not installed the game still runs — the dice roll animation falls back to a static frame shuffle.
