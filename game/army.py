"""
Army management for Strategic Conquest
Handles army units, their properties and states
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Army:
    """Represents an army unit in the game"""
    
    x: int  # X position on the board
    y: int  # Y position on the board
    strength: int  # Army size (1-100)
    food: int  # Food supply
    has_general: bool  # Whether this army has a general
    player_id: int  # ID of the player who controls this army
    
    # State flags for turn management
    moved_this_turn: bool = field(default=False)
    fought_this_turn: bool = field(default=False)
    
    def __post_init__(self):
        """Validate initialization data"""
        # Ensure army strength stays within bounds
        self.strength = max(0, min(100, self.strength))
        
        # Ensure food is non-negative
        self.food = max(0, self.food)
        
    def get_movement_tier(self) -> int:
        """Get movement tier based on army size"""
        if self.strength <= 25:
            return 4  # Fastest
        elif self.strength <= 50:
            return 3
        elif self.strength <= 75:
            return 2
        else:
            return 1  # Slowest
    
    def calculate_combat_power(self) -> float:
        """Calculate the combat power of this army, accounting for general"""
        base_power = self.strength
        general_bonus = 1.25 if self.has_general else 1.0
        return base_power * general_bonus
        
    def can_split(self) -> bool:
        """Check if this army can be split"""
        return self.strength > 1 and self.food > 1
        
    def __str__(self) -> str:
        general_symbol = "★" if self.has_general else ""
        return f"Army P{self.player_id}({self.strength}{general_symbol}, {self.food}f)"
        
    def __repr__(self) -> str:
        return self.__str__()
