# vibe_coding_bootcamp

Mini Galaga-style arcade shooter built with `pygame` as part of the Vibe Coding Bootcamp.

## Prerequisites
- Python 3.10+ (project developed against CPython 3.11)
- `pip` for dependency management
- macOS, Windows, or Linux with a GPU capable of running a 2D pygame window

## Setup & Run
1. Optional: create and activate a virtual environment  
   - `python -m venv .venv`  
   - `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
2. Install dependencies: `pip install pygame`
3. Launch the game window: `python galaga.py`

### Controls
- `← / →` move the player ship
- `SPACE` fire
- `ESC` quit mid-game

## Repository Layout
- `galaga.py` – full game implementation, including resource loading, entities, loop logic, and collision handling
- `assets/` – optional directory for overriding sprites (`player.png`, `enemy.png`, `player_bullet.png`, `enemy_bullet.png`) and font (`galaga.ttf`); procedurally generated fallbacks are used when files are missing

## Progress Log
1. Bootstrapped project with configuration constants for screen, entities, and timing.
2. Added resource helpers to load sprites or fall back to procedurally generated surfaces and fonts.
3. Implemented reusable dataclasses (`Entity`, `Bullet`, `Enemy`) to simplify drawing and updating actors.
4. Built a scrolling `StarField` background to match the arcade aesthetic.
5. Created sprite factories that procedurally render default player, enemy, and projectile art.
6. Developed the `GalagaGame` class to encapsulate initialisation, main loop, event handling, updates, and rendering.
7. Implemented gameplay systems: player movement and shooting cooldown, enemy wave spawning with sine-wave motion, bullet lifecycle, scoring, lives, and collision detection.
8. Added a simple HUD and game-over state handling, plus an executable entry point.

## Next Steps
- Add sound effects and background music
- Introduce power-ups and varied enemy behaviours
- Package dependencies in `requirements.txt` or Poetry for reproducible installs
