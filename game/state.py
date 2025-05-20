"""
Game state management for Strategic Conquest
Handles core game logic, turn management, and state transitions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import yaml
import os

from game.board import Board, Tile, TileType
from game.army import Army


class Player:
    """Represents a player in the game"""
    
    def __init__(self, player_id: int, name: str, color: Tuple[int, int, int]):
        self.id = player_id
        self.name = name
        self.color = color
        self.score = 0
        self.armies: List[Army] = []
        self.headquarters_position: Optional[Tuple[int, int]] = None
        self.is_eliminated = False
        
    def add_army(self, army: 'Army'):
        """Add an army to this player's control"""
        self.armies.append(army)
        army.player_id = self.id
        
    def remove_army(self, army: 'Army'):
        """Remove an army from this player's control"""
        if army in self.armies:
            self.armies.remove(army)
            
    def calculate_visibility(self, board: Board) -> Set[Tuple[int, int]]:
        """Calculate all tiles visible to this player's armies"""
        visible_tiles = set()
        
        for army in self.armies:
            # Get base visibility range based on the army's position
            tile = board.get_tile(army.x, army.y)
            base_range = self.config['visibility']['base_range']
            
            # Adjust for terrain
            if tile.type == TileType.FOREST:
                range_mod = self.config['visibility']['forest_penalty']
            elif tile.type == TileType.MOUNTAIN:
                range_mod = self.config['visibility']['mountain_bonus']
            else:
                range_mod = 0
                
            visibility_range = max(1, base_range + range_mod)
            
            # Add all tiles within visibility range
            for dx in range(-visibility_range, visibility_range + 1):
                for dy in range(-visibility_range, visibility_range + 1):
                    # Calculate distance (Manhattan for simplicity)
                    distance = abs(dx) + abs(dy)
                    if distance <= visibility_range:
                        visible_x, visible_y = army.x + dx, army.y + dy
                        if board.is_valid_position(visible_x, visible_y):
                            visible_tiles.add((visible_x, visible_y))
        
        return visible_tiles


class GameState:
    """Manages the overall state of the game"""
    
    def __init__(self, board: Board, num_players: int = 2):
        # Load configuration
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.board = board
        self.players: List[Player] = []
        self.current_player_index = 0
        self.turn_number = 1
        self.game_over = False
        self.winner = None
        self.selected_army = None
        
        # Initialize players
        player_colors = self.config['colors']['players']
        for i in range(num_players):
            player = Player(i, f"Player {i+1}", player_colors[i])
            self.players.append(player)
            
        # Set up initial game state
        self._setup_game()
        
    def _setup_game(self):
        """Initialize the board and place starting armies"""
        # Create a basic board layout
        self.board.generate_random_map(
            fort_count=5,
            forest_percentage=0.2,
            river_count=2,
            mountain_percentage=0.1
        )
        
        # Place headquarters and initial armies for each player
        headquarters_positions = [
            (1, 1),                                          # Top-left
            (self.board.width - 2, self.board.height - 2),   # Bottom-right
            (1, self.board.height - 2),                      # Bottom-left
            (self.board.width - 2, 1)                        # Top-right
        ]
        
        for i, player in enumerate(self.players):
            # Set headquarters position for this player
            hq_x, hq_y = headquarters_positions[i]
            player.headquarters_position = (hq_x, hq_y)
            
            # Set the tile to headquarters type
            self.board.get_tile(hq_x, hq_y).type = TileType.HEADQUARTERS
            
            # Create initial army
            starting_size = self.config['game']['starting_army_size']
            starting_food = self.config['game']['starting_food']
            
            army = Army(
                x=hq_x,
                y=hq_y,
                strength=starting_size,
                food=starting_food,
                has_general=True,
                player_id=player.id
            )
            
            player.add_army(army)
            self.board.add_army(army)
    
    def get_current_player(self) -> Player:
        """Get the player whose turn it currently is"""
        return self.players[self.current_player_index]
    
    def next_turn(self):
        """Advance to the next player's turn"""
        # Process end-of-turn effects for current player
        self._process_end_of_turn()
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # Skip eliminated players
        while self.players[self.current_player_index].is_eliminated:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            
            # If we've gone full circle and all players are eliminated, end the game
            if self.current_player_index == 0:
                self.game_over = True
                self._determine_winner()
                break
                
        # If we've returned to player 0, increment turn counter
        if self.current_player_index == 0:
            self.turn_number += 1
            
            # Check turn limit
            if self.turn_number > self.config['game']['turn_limit']:
                self.game_over = True
                self._determine_winner()
    
    def _process_end_of_turn(self):
        """Process all end-of-turn effects"""
        player = self.get_current_player()
        
        # Process supply and food consumption
        for army in player.armies:
            # Check if army is in supply
            is_supplied = self._check_supply(army)
            
            # Consume food based on activity
            if army.moved_this_turn and army.fought_this_turn:
                food_consumption = self.config['supply']['consumption']['combat']
            elif army.moved_this_turn:
                food_consumption = self.config['supply']['consumption']['moving']
            else:
                food_consumption = self.config['supply']['consumption']['stationary']
                
            army.food -= food_consumption
            
            # If out of food, start losing strength
            if army.food <= 0:
                # Convert negative food to strength loss
                strength_loss = min(abs(army.food) + 1, army.strength)
                army.strength -= strength_loss
                army.food = 0
                
            # Generate food if on a fort
            tile = self.board.get_tile(army.x, army.y)
            if tile.type == TileType.FORT:
                food_gen = self.config['tiles']['fort']['food_generation']
                army.food += food_gen
                
            # Resupply if at headquarters
            if tile.type == TileType.HEADQUARTERS and tile.player_id == player.id:
                army.food = self.config['game']['starting_food']
                
            # Reset turn flags
            army.moved_this_turn = False
            army.fought_this_turn = False
            
            # Remove armies with zero strength
            if army.strength <= 0:
                self.board.remove_army(army)
                player.remove_army(army)
        
        # Check if player is eliminated (no armies left)
        if not player.armies:
            player.is_eliminated = True
            
        # Check for control of forts and add points
        for x in range(self.board.width):
            for y in range(self.board.height):
                tile = self.board.get_tile(x, y)
                if tile.type == TileType.FORT:
                    armies_on_tile = self.board.get_armies_at(x, y)
                    if armies_on_tile and all(a.player_id == player.id for a in armies_on_tile):
                        player.score += self.config['scoring']['fort_control']
    
    def _check_supply(self, army: Army) -> bool:
        """Check if an army is in supply (connected to HQ)"""
        player = self.players[army.player_id]
        
        # If at headquarters, automatically in supply
        tile = self.board.get_tile(army.x, army.y)
        if tile.type == TileType.HEADQUARTERS and tile.player_id == player.id:
            return True
            
        # Check direct distance to headquarters
        hq_x, hq_y = player.headquarters_position
        distance = abs(army.x - hq_x) + abs(army.y - hq_y)
        supply_range = self.config['supply']['base_range']
        
        if distance <= supply_range:
            return True
            
        # TODO: Implement supply chain checking (connect through friendly units)
        # This would require pathfinding algorithms from NetworkX
        
        return False
    
    def _determine_winner(self):
        """Determine the winner based on scores"""
        if not self.game_over:
            return
            
        # Find player with highest score
        max_score = -1
        winner = None
        
        for player in self.players:
            if player.score > max_score:
                max_score = player.score
                winner = player
                
        self.winner = winner
    
    def move_army(self, army: Army, new_x: int, new_y: int) -> bool:
        """
        Move an army to a new position if valid
        Returns True if successful, False otherwise
        """
        if not self.board.is_valid_position(new_x, new_y):
            return False
            
        # Check if the move is within range
        movement_range = self._calculate_movement_range(army)
        if abs(new_x - army.x) + abs(new_y - army.y) > movement_range:
            return False
            
        # Update position
        old_x, old_y = army.x, army.y
        army.x, army.y = new_x, new_y
        
        # Mark as moved this turn
        army.moved_this_turn = True
        
        # Update board representation
        self.board.move_army(army, old_x, old_y, new_x, new_y)
        
        return True
    
    def _calculate_movement_range(self, army: Army) -> int:
        """Calculate how far an army can move based on its size and general"""
        # Find the appropriate movement tier
        movement_tiers = self.config['movement']['tiers']
        base_movement = 1  # Default if no tier matches
        
        for tier in movement_tiers:
            if tier['min'] <= army.strength <= tier['max']:
                base_movement = tier['speed']
                break
                
        # Apply general bonus if applicable
        general_bonus = self.config['movement']['general_bonus'] if army.has_general else 0
        
        # TODO: Apply terrain modifiers based on current tile
        
        return base_movement + general_bonus
    
    def split_army(self, army: Army, new_strength: int, new_food: int, 
                  keep_general: bool, new_x: int, new_y: int) -> Optional[Army]:
        """
        Split an existing army into two parts
        Returns the newly created army if successful, None otherwise
        """
        # Validate parameters
        if new_strength <= 0 or new_strength >= army.strength:
            return None
            
        if new_food <= 0 or new_food >= army.food:
            return None
            
        # Check if target position is adjacent and valid
        if not self.board.is_valid_position(new_x, new_y):
            return None
            
        if abs(new_x - army.x) + abs(new_y - army.y) != 1:
            return None
            
        # Create new army
        new_army = Army(
            x=new_x,
            y=new_y,
            strength=new_strength,
            food=new_food,
            has_general=keep_general and army.has_general,
            player_id=army.player_id
        )
        
        # Update original army
        army.strength -= new_strength
        army.food -= new_food
        if keep_general:
            army.has_general = False
            
        # Add new army to board and player
        self.board.add_army(new_army)
        player = self.players[army.player_id]
        player.add_army(new_army)
        
        # Mark both armies as moved this turn
        army.moved_this_turn = True
        new_army.moved_this_turn = True
        
        return new_army
    
    def merge_armies(self, army1: Army, army2: Army) -> bool:
        """
        Merge two adjacent armies into one
        Returns True if successful, False otherwise
        """
        # Verify the armies belong to the same player
        if army1.player_id != army2.player_id:
            return False
            
        # Check if they are adjacent
        if abs(army1.x - army2.x) + abs(army1.y - army2.y) != 1:
            return False
            
        # Combine strength and food
        army1.strength += army2.strength
        army1.food += army2.food
        
        # If either had a general, the combined force has a general
        if army1.has_general or army2.has_general:
            army1.has_general = True
            
        # Remove the second army
        self.board.remove_army(army2)
        player = self.players[army2.player_id]
        player.remove_army(army2)
        
        # Mark as moved this turn
        army1.moved_this_turn = True
        
        return True
    
    def retreat_army(self, army: Army) -> bool:
        """
        Retreat an army through headquarters if possible
        Returns True if successful, False otherwise
        """
        # Check if the army is at its headquarters
        player = self.players[army.player_id]
        hq_x, hq_y = player.headquarters_position
        
        if army.x != hq_x or army.y != hq_y:
            return False
            
        # Remove the army from the game
        self.board.remove_army(army)
        player.remove_army(army)
        
        return True
    
    def update(self):
        """Update game state (for animations, etc.)"""
        # Process combat between armies of different players
        self._resolve_combat()
        
        # Check for game over conditions
        self._check_game_over()
    
    def _resolve_combat(self):
        """Resolve combat between opposing armies"""
        # Get all positions with armies
        positions_with_armies = {}
        for x in range(self.board.width):
            for y in range(self.board.height):
                armies = self.board.get_armies_at(x, y)
                if armies:
                    positions_with_armies[(x, y)] = armies
        
        # Find positions with armies from different players (contact positions)
        contact_positions = []
        for pos, armies in positions_with_armies.items():
            player_ids = set(army.player_id for army in armies)
            if len(player_ids) > 1:
                contact_positions.append(pos)
                
        # Process combat at each contact position
        for x, y in contact_positions:
            armies = self.board.get_armies_at(x, y)
            self._process_combat_at_position(x, y, armies)
                
    def _process_combat_at_position(self, x: int, y: int, armies: List[Army]):
        """Process combat between armies at a specific position"""
        # Group armies by player
        armies_by_player = {}
        for army in armies:
            if army.player_id not in armies_by_player:
                armies_by_player[army.player_id] = []
            armies_by_player[army.player_id].append(army)
            
        # Calculate total strength per player
        strength_by_player = {}
        has_general_by_player = {}
        for player_id, player_armies in armies_by_player.items():
            strength_by_player[player_id] = sum(army.strength for army in player_armies)
            has_general_by_player[player_id] = any(army.has_general for army in player_armies)
            
        # Calculate strength differences and apply combat effects
        for attacker_id, attacker_armies in armies_by_player.items():
            for defender_id, defender_armies in armies_by_player.items():
                if attacker_id != defender_id:
                    attacker_strength = strength_by_player[attacker_id]
                    defender_strength = strength_by_player[defender_id]
                    
                    # Calculate base damage (percentage of opponent's strength)
                    base_attrition = self.config['combat']['base_attrition']
                    
                    # Size difference penalty
                    size_difference = max(0, defender_strength - attacker_strength)
                    size_penalty = self.config['combat']['size_penalty'] * (size_difference / 20)
                    
                    # General bonus
                    attacker_general_bonus = self.config['combat']['general_bonus'] if has_general_by_player[attacker_id] else 0
                    
                    # TODO: Account for flanking and terrain
                    
                    # Calculate final damage percentage
                    damage_percentage = base_attrition + attacker_general_bonus
                    
                    # Calculate damage dealt
                    damage = int(attacker_strength * damage_percentage)
                    
                    # Apply damage proportionally to defender's armies
                    self._apply_damage_to_armies(defender_armies, damage)
                    
                    # Mark armies as having fought this turn
                    for army in attacker_armies + defender_armies:
                        army.fought_this_turn = True
                        
    def _apply_damage_to_armies(self, armies: List[Army], total_damage: int):
        """Apply damage proportionally across multiple armies"""
        # Calculate total strength
        total_strength = sum(army.strength for army in armies)
        if total_strength <= 0:
            return
            
        # Distribute damage proportionally
        remaining_damage = total_damage
        
        for army in armies:
            # Calculate proportional damage
            proportion = army.strength / total_strength
            army_damage = min(int(remaining_damage * proportion), army.strength)
            
            # Apply damage
            army.strength -= army_damage
            remaining_damage -= army_damage
            
            # Check if any armies were eliminated
            eliminated_armies = [army for army in armies if army.strength <= 0]
            for eliminated in eliminated_armies:
                # Award points to all players who dealt damage to this army
                for player in self.players:
                    if player.id != eliminated.player_id:
                        # Check if any of this player's armies are in contact
                        is_in_contact = False
                        for player_army in player.armies:
                            if abs(player_army.x - eliminated.x) + abs(player_army.y - eliminated.y) <= 1:
                                is_in_contact = True
                                break
                                
                        if is_in_contact:
                            elimination_points = int(self.config['scoring']['elimination_factor'] * eliminated.strength)
                            player.score += elimination_points
                            
                # Remove the eliminated army
                self.board.remove_army(eliminated)
                self.players[eliminated.player_id].remove_army(eliminated)
                
    def _check_game_over(self):
        """Check if game over conditions have been met"""
        # Count active players
        active_players = sum(1 for player in self.players if not player.is_eliminated)
        
        # Game over if only one player remains
        if active_players <= 1:
            self.game_over = True
            self._determine_winner()
            
        # Check turn limit
        if self.turn_number > self.config['game']['turn_limit']:
            self.game_over = True
            self._determine_winner()
