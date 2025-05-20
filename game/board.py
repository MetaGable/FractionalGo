"""
Board management for Strategic Conquest
Handles the game board, tiles, and unit positions
"""

from enum import Enum, auto
from typing import List, Dict, Optional, Set, Tuple
import random
import numpy as np


class TileType(Enum):
    """Types of tiles on the board"""
    PLAIN = auto()
    HEADQUARTERS = auto()
    FORT = auto()
    FOREST = auto()
    VALLEY = auto()
    RIVER = auto()
    MOUNTAIN = auto()
    
    @classmethod
    def from_string(cls, name: str) -> 'TileType':
        """Convert string to tile type enum"""
        name = name.upper()
        if hasattr(cls, name):
            return getattr(cls, name)
        return cls.PLAIN


class Tile:
    """Represents a single tile on the board"""
    
    def __init__(self, x: int, y: int, tile_type: TileType = TileType.PLAIN):
        self.x = x
        self.y = y
        self.type = tile_type
        self.player_id: Optional[int] = None  # For headquarters ownership
        
    def __str__(self):
        return f"Tile({self.x}, {self.y}, {self.type.name})"


class Board:
    """Represents the game board"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles: List[List[Tile]] = []
        self.armies_by_position: Dict[Tuple[int, int], List['Army']] = {}
        
        # Initialize empty board
        self._initialize_board()
        
    def _initialize_board(self):
        """Initialize the board with plain tiles"""
        self.tiles = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(Tile(x, y, TileType.PLAIN))
            self.tiles.append(row)
            
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is valid on the board"""
        return 0 <= x < self.width and 0 <= y < self.height
        
    def get_tile(self, x: int, y: int) -> Tile:
        """Get the tile at a specific position"""
        if not self.is_valid_position(x, y):
            raise ValueError(f"Invalid position: ({x}, {y})")
        return self.tiles[y][x]
        
    def set_tile_type(self, x: int, y: int, tile_type: TileType):
        """Set the type of a tile at a specific position"""
        if not self.is_valid_position(x, y):
            raise ValueError(f"Invalid position: ({x}, {y})")
        self.tiles[y][x].type = tile_type
        
    def add_army(self, army: 'Army'):
        """Add an army to the board"""
        pos = (army.x, army.y)
        if pos not in self.armies_by_position:
            self.armies_by_position[pos] = []
        self.armies_by_position[pos].append(army)
        
    def remove_army(self, army: 'Army'):
        """Remove an army from the board"""
        pos = (army.x, army.y)
        if pos in self.armies_by_position and army in self.armies_by_position[pos]:
            self.armies_by_position[pos].remove(army)
            if not self.armies_by_position[pos]:
                del self.armies_by_position[pos]
                
    def move_army(self, army: 'Army', old_x: int, old_y: int, new_x: int, new_y: int):
        """Update army position on the board"""
        old_pos = (old_x, old_y)
        new_pos = (new_x, new_y)
        
        # Remove from old position
        if old_pos in self.armies_by_position and army in self.armies_by_position[old_pos]:
            self.armies_by_position[old_pos].remove(army)
            if not self.armies_by_position[old_pos]:
                del self.armies_by_position[old_pos]
                
        # Add to new position
        if new_pos not in self.armies_by_position:
            self.armies_by_position[new_pos] = []
        self.armies_by_position[new_pos].append(army)
        
    def get_armies_at(self, x: int, y: int) -> List['Army']:
        """Get all armies at a specific position"""
        pos = (x, y)
        return self.armies_by_position.get(pos, [])
        
    def get_adjacent_positions(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get all valid adjacent positions (orthoganally connected)"""
        adjacent = [
            (x-1, y), (x+1, y), (x, y-1), (x, y+1)
        ]
        return [pos for pos in adjacent if self.is_valid_position(pos[0], pos[1])]
        
    def get_adjacent_armies(self, x: int, y: int) -> List['Army']:
        """Get all armies adjacent to a position"""
        armies = []
        for adj_x, adj_y in self.get_adjacent_positions(x, y):
            armies.extend(self.get_armies_at(adj_x, adj_y))
        return armies
        
    def generate_random_map(self, fort_count: int = 5, forest_percentage: float = 0.2, 
                           river_count: int = 2, mountain_percentage: float = 0.1):
        """Generate a random map layout"""
        # Reset the board to all plains
        self._initialize_board()
        
        # Place forts (evenly distributed)
        fort_positions = self._generate_distributed_positions(fort_count)
        for x, y in fort_positions:
            self.set_tile_type(x, y, TileType.FORT)
            
        # Add forests (in clumps)
        forest_count = int(self.width * self.height * forest_percentage)
        self._generate_clumped_terrain(forest_count, TileType.FOREST, clump_factor=0.7)
            
        # Add mountains (in clumps)
        mountain_count = int(self.width * self.height * mountain_percentage)
        self._generate_clumped_terrain(mountain_count, TileType.MOUNTAIN, clump_factor=0.6)
            
        # Add rivers
        for _ in range(river_count):
            self._generate_river()
            
    def _generate_distributed_positions(self, count: int) -> List[Tuple[int, int]]:
        """Generate evenly distributed positions on the map"""
        positions = []
        
        # Divide the map into regions
        if count <= 1:
            regions = [(0, 0, self.width, self.height)]
        else:
            # Try to create a grid of regions
            grid_size = int(np.ceil(np.sqrt(count)))
            region_width = self.width // grid_size
            region_height = self.height // grid_size
            
            regions = []
            for i in range(grid_size):
                for j in range(grid_size):
                    x_start = i * region_width
                    y_start = j * region_height
                    x_end = min((i + 1) * region_width, self.width)
                    y_end = min((j + 1) * region_height, self.height)
                    regions.append((x_start, y_start, x_end, y_end))
                    
                    if len(regions) >= count:
                        break
                if len(regions) >= count:
                    break
                    
        # Place one position in each region
        for x_start, y_start, x_end, y_end in regions[:count]:
            # Add some randomness within the region
            margin = 2  # Stay away from the edges
            x = random.randint(x_start + margin, x_end - margin - 1) if x_end - x_start > 2*margin else (x_start + x_end) // 2
            y = random.randint(y_start + margin, y_end - margin - 1) if y_end - y_start > 2*margin else (y_start + y_end) // 2
            
            positions.append((x, y))
            
        return positions
        
    def _generate_clumped_terrain(self, count: int, tile_type: TileType, clump_factor: float = 0.5):
        """Generate terrain features in clumps"""
        if count <= 0:
            return
            
        # Start with random seed points
        seed_count = max(1, int(count * (1 - clump_factor)))
        positions = set()
        
        while len(positions) < seed_count:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            # Don't place on headquarters or forts
            tile = self.get_tile(x, y)
            if tile.type not in (TileType.HEADQUARTERS, TileType.FORT):
                positions.add((x, y))
                
        # Grow clusters
        while len(positions) < count:
            # Pick a random existing position
            if not positions:
                break
                
            seed_x, seed_y = random.choice(list(positions))
            
            # Get adjacent positions
            adjacent = self.get_adjacent_positions(seed_x, seed_y)
            valid_adjacent = []
            
            for adj_x, adj_y in adjacent:
                # Check if position is already used or is HQ/fort
                if (adj_x, adj_y) in positions:
                    continue
                    
                tile = self.get_tile(adj_x, adj_y)
                if tile.type in (TileType.HEADQUARTERS, TileType.FORT, tile_type):
                    continue
                    
                valid_adjacent.append((adj_x, adj_y))
                
            # Add a random adjacent position
            if valid_adjacent:
                positions.add(random.choice(valid_adjacent))
                
        # Set tile types
        for x, y in positions:
            self.set_tile_type(x, y, tile_type)
            
    def _generate_river(self):
        """Generate a river across the map"""
        # Decide direction (horizontal or vertical)
        is_horizontal = random.choice([True, False])
        
        if is_horizontal:
            # Start from left or right
            start_from_left = random.choice([True, False])
            
            # Pick a row
            y = random.randint(2, self.height - 3)
            
            # Generate river path
            x = 0 if start_from_left else self.width - 1
            river_tiles = []
            
            while 0 <= x < self.width:
                river_tiles.append((x, y))
                
                # Move forward
                x = x + 1 if start_from_left else x - 1
                
                # Occasionally change y
                if random.random() < 0.2:
                    y_change = random.choice([-1, 1])
                    new_y = y + y_change
                    
                    if 1 <= new_y < self.height - 1:
                        y = new_y
        else:
            # Start from top or bottom
            start_from_top = random.choice([True, False])
            
            # Pick a column
            x = random.randint(2, self.width - 3)
            
            # Generate river path
            y = 0 if start_from_top else self.height - 1
            river_tiles = []
            
            while 0 <= y < self.height:
                river_tiles.append((x, y))
                
                # Move forward
                y = y + 1 if start_from_top else y - 1
                
                # Occasionally change x
                if random.random() < 0.2:
                    x_change = random.choice([-1, 1])
                    new_x = x + x_change
                    
                    if 1 <= new_x < self.width - 1:
                        x = new_x
                        
        # Set river tiles
        for rx, ry in river_tiles:
            tile = self.get_tile(rx, ry)
            if tile.type not in (TileType.HEADQUARTERS, TileType.FORT):
                self.set_tile_type(rx, ry, TileType.RIVER)
