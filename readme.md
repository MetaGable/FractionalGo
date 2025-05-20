# Strategic Conquest

A territorial wargame with dynamic armies, inspired by Go but with unique mechanics for army management and supply lines.

## Game Overview

Strategic Conquest is a turn-based strategy game for 2-4 players. The objective is to score the most points by eliminating enemy armies and controlling fort tiles. Each player commands one or more armies that can be split, merged, and maneuvered across the map.

Key features include:
- Dynamic army management with splitting and merging
- Supply lines and food resource management
- Combat system with generals providing bonuses
- Fog of war and visibility mechanics
- Various terrain types affecting movement and combat

## Installation

### Prerequisites

- Python 3.7+
- Pygame
- Pygame_GUI
- NumPy
- NetworkX
- PyYAML

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/strategic-conquest.git
cd strategic-conquest
```

2. Install dependencies:
```bash
pip install pygame pygame_gui numpy networkx pyyaml
```

3. Run the game:
```bash
python main.py
```

## How to Play

### Basic Controls
- **Left Click**: Select a tile or army
- **Left Click (on highlighted tile)**: Move selected army to that tile
- **End Turn Button**: End your turn
- **Split Button**: Split a selected army
- **Merge Button**: Merge multiple armies on the same tile
- **Retreat Button**: Retreat an army through headquarters

### Game Mechanics

#### Armies
- Armies have two main resources: **Strength** (1-100) and **Food**
- Smaller armies move faster, while larger armies are more powerful in combat
- Armies can split and occupy neighboring tiles
- Separate armies can merge when adjacent
- Each army may have a **General** that provides bonuses to combat and movement

#### Movement
- Movement range depends on army size:
  - 1-25 soldiers: 4 tiles per turn
  - 26-50 soldiers: 3 tiles per turn
  - 51-75 soldiers: 2 tiles per turn
  - 76-100 soldiers: 1 tile per turn
- Armies with generals get +1 movement

#### Supply and Food
- Food depletes each turn
- Movement and combat consume more food
- When food reaches zero, army strength begins to diminish
- Armies can be resupplied by being:
  - Near headquarters
  - Connected to headquarters through a chain of friendly armies

#### Combat
- Combat occurs automatically when armies of different players occupy the same tile
- Both sides lose strength each turn in contact
- Smaller armies lose strength faster
- Generals provide a combat bonus
- Flanking (attacking with multiple armies) increases damage

#### Scoring
- Eliminating enemy armies: 1 point per 10 strength eliminated
- Controlling fort tiles: 5 points per fort at turn end
- Capturing an enemy headquarters: 15 points

### Tile Types
- **Headquarters**: Spawn point, retreat location, supply source
- **Plain**: Standard terrain
- **Fort**: Defensive bonus, generates food, worth points when controlled
- **Forest**: Reduced visibility, slower movement, defensive bonus
- **Valley**: No special effects
- **River**: Slower movement
- **Mountain**: Slower movement, visibility bonus, defensive bonus

## Project Structure

The game is organized into several modules:

```
strategic_conquest/
│
├── main.py                  # Entry point, game loop
├── config.yaml              # Game parameters and configuration
│
├── game/                    # Core game mechanics
│   ├── __init__.py
│   ├── state.py             # Game state management
│   ├── board.py             # Board and tile functionality
│   └── army.py              # Army class and mechanics
│
├── ui/                      # User interface
│   ├── __init__.py
│   ├── renderer.py          # Game rendering
│   └── controls.py          # UI controls
│
└── utils/                   # Utilities
    ├── __init__.py
    ├── pathfinding.py       # Movement calculations
    └── serialization.py     # Save/load functionality
```

## Customization

You can customize the game by modifying the `config.yaml` file, which contains settings for:
- Board size
- Starting army size and food
- Movement tiers
- Combat parameters
- Supply mechanics
- Scoring values
- Terrain effects
- Colors for UI and players

## Future Enhancements

Planned features for future updates:
- AI opponents
- Network multiplayer
- More terrain types
- Special abilities
- Campaign mode with scenarios
- Custom map editor

## License

[MIT License](LICENSE)
