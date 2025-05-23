"""
Renderer for Strategic Conquest
Handles the visual display of the game state
"""

import pygame
import yaml
from typing import Dict, Tuple, List, Optional, Set
import math

from game.state import GameState
from game.board import TileType
from game.army import Army


class GameRenderer:
    """Renders the game state to the screen"""
    
    def __init__(self, screen: pygame.Surface, game_state: GameState):
        self.screen = screen
        self.game_state = game_state
        
        # Load configuration
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Calculate tile size based on screen and board dimensions
        screen_width, screen_height = screen.get_size()
        board_width, board_height = game_state.board.width, game_state.board.height
        
        # Set up dimensions
        self.tile_size = self.config['board']['tile_size']
        self.board_pixel_width = board_width * self.tile_size
        self.board_pixel_height = board_height * self.tile_size
        
        # Calculate offsets to center the board
        self.offset_x = (screen_width - self.board_pixel_width) // 2
        self.offset_y = (screen_height - self.board_pixel_height) // 2
        
        # UI state
        self.selected_position: Optional[Tuple[int, int]] = None
        self.highlighted_positions: Set[Tuple[int, int]] = set()
        self.visible_positions: Dict[int, Set[Tuple[int, int]]] = {}  # Player ID -> visible positions
        
        # Load colors
        self.tile_colors = {
            TileType.PLAIN: self._parse_color(self.config['colors']['tiles']['plain']),
            TileType.HEADQUARTERS: self._parse_color(self.config['colors']['tiles']['headquarters']),
            TileType.FORT: self._parse_color(self.config['colors']['tiles']['fort']),
            TileType.FOREST: self._parse_color(self.config['colors']['tiles']['forest']),
            TileType.VALLEY: self._parse_color(self.config['colors']['tiles']['valley']),
            TileType.RIVER: self._parse_color(self.config['colors']['tiles']['river']),
            TileType.MOUNTAIN: self._parse_color(self.config['colors']['tiles']['mountain'])
        }
        
        self.player_colors = [self._parse_color(color) for color in self.config['colors']['players']]
        self.selection_color = self._parse_color(self.config['colors']['ui']['selection'])
        self.highlight_color = self._parse_color(self.config['colors']['ui']['highlight'])
        
        # Initialize fonts
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 12)
        self.large_font = pygame.font.SysFont('Arial', 16, bold=True)
        
    def _parse_color(self, color_list: List[int]) -> Tuple[int, int, int]:
        """Convert a color list to a tuple"""
        return tuple(color_list)
        
    def render(self):
        """Render the entire game state"""
        self._render_board()
        self._render_armies()
        self._render_ui()
        
    def _render_board(self):
        """Render the game board"""
        # Calculate visibility for current player
        current_player = self.game_state.get_current_player()
        self.visible_positions[current_player.id] = current_player.calculate_visibility(self.game_state.board, self.config)
        
        # Draw tiles
        for y in range(self.game_state.board.height):
            for x in range(self.game_state.board.width):
                # Get tile type
                tile = self.game_state.board.get_tile(x, y)
                
                # Determine visibility
                is_visible = (x, y) in self.visible_positions[current_player.id]
                fog_factor = 1.0 if is_visible else 0.5
                
                # Get base color for tile type
                color = self.tile_colors[tile.type]
                
                # Apply fog of war
                if not is_visible:
                    color = tuple(int(c * fog_factor) for c in color)
                
                # Draw tile
                rect = pygame.Rect(
                    self.offset_x + x * self.tile_size,
                    self.offset_y + y * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)  # Border
                
                # Draw selection highlight
                if (x, y) == self.selected_position:
                    pygame.draw.rect(self.screen, self.selection_color, rect, 3)
                    
                # Draw movement highlights
                if (x, y) in self.highlighted_positions:
                    pygame.draw.rect(self.screen, self.highlight_color, rect, 2)
                    
                # Draw tile type indicator
                if tile.type != TileType.PLAIN:
                    symbol = self._get_tile_symbol(tile.type)
                    text = self.font.render(symbol, True, (0, 0, 0))
                    text_rect = text.get_rect(center=(
                        self.offset_x + x * self.tile_size + self.tile_size // 2,
                        self.offset_y + y * self.tile_size + self.tile_size // 2
                    ))
                    self.screen.blit(text, text_rect)
                    
    def _get_tile_symbol(self, tile_type: TileType) -> str:
        """Get a symbol to represent a tile type"""
        if tile_type == TileType.HEADQUARTERS:
            return "HQ"
        elif tile_type == TileType.FORT:
            return "F"
        elif tile_type == TileType.FOREST:
            return "🌲"
        elif tile_type == TileType.VALLEY:
            return "V"
        elif tile_type == TileType.RIVER:
            return "~"
        elif tile_type == TileType.MOUNTAIN:
            return "▲"
        return ""
        
    def _render_armies(self):
        """Render all armies on the board"""
        current_player = self.game_state.get_current_player()
        
        for (x, y), armies in self.game_state.board.armies_by_position.items():
            # Check if position is visible to current player
            is_visible = (x, y) in self.visible_positions[current_player.id]
            
            if is_visible or any(army.player_id == current_player.id for army in armies):
                self._render_armies_at_position(x, y, armies)
                
    def _render_armies_at_position(self, x: int, y: int, armies: List[Army]):
        """Render armies at a specific position"""
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
            
        # Get number of players at this position
        num_players = len(armies_by_player)
        
        # Determine how to arrange the armies
        if num_players == 1:
            # Single player - draw one circle
            player_id = list(armies_by_player.keys())[0]
            strength = strength_by_player[player_id]
            has_general = has_general_by_player[player_id]
            
            center_x = self.offset_x + x * self.tile_size + self.tile_size // 2
            center_y = self.offset_y + y * self.tile_size + self.tile_size // 2
            
            self._draw_army(center_x, center_y, player_id, strength, has_general)
        else:
            # Multiple players - divide the tile
            positions = [
                (0.25, 0.25),  # Top-left
                (0.75, 0.25),  # Top-right
                (0.25, 0.75),  # Bottom-left
                (0.75, 0.75)   # Bottom-right
            ]
            
            for i, (player_id, player_armies) in enumerate(armies_by_player.items()):
                if i >= len(positions):
                    break
                    
                rel_x, rel_y = positions[i]
                center_x = self.offset_x + x * self.tile_size + int(rel_x * self.tile_size)
                center_y = self.offset_y + y * self.tile_size + int(rel_y * self.tile_size)
                
                strength = strength_by_player[player_id]
                has_general = has_general_by_player[player_id]
                
                self._draw_army(center_x, center_y, player_id, strength, has_general, size_factor=0.7)
                
    def _draw_army(self, center_x: int, center_y: int, player_id: int, strength: int, 
                  has_general: bool, size_factor: float = 1.0):
        """Draw an army representation"""
        # Calculate radius based on strength
        max_radius = self.tile_size // 3 * size_factor
        min_radius = max_radius // 2
        radius = min_radius + (max_radius - min_radius) * min(1.0, strength / 50)
        
        # Draw circle for the army
        color = self.player_colors[player_id % len(self.player_colors)]
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, (0, 0, 0), (center_x, center_y), radius, 1)
        
        # Draw strength number
        text = self.font.render(str(strength), True, (0, 0, 0))
        text_rect = text.get_rect(center=(center_x, center_y))
        self.screen.blit(text, text_rect)
        
        # Draw general indicator
        if has_general:
            pygame.draw.circle(self.screen, (255, 255, 255), (center_x, center_y - int(radius * 0.7)), 3)
            
    def _render_ui(self):
        """Render UI elements"""
        # Draw game status
        self._render_game_status()
        
        # Draw selected unit info
        if self.selected_position:
            self._render_selected_info()
            
    def _render_game_status(self):
        """Render game status information"""
        # Draw current player indicator
        current_player = self.game_state.get_current_player()
        player_color = self.player_colors[current_player.id % len(self.player_colors)]
        
        # Draw turn indicator
        turn_text = f"Turn {self.game_state.turn_number}"
        player_text = f"Player {current_player.id + 1}"
        
        turn_surface = self.large_font.render(turn_text, True, (255, 255, 255))
        player_surface = self.large_font.render(player_text, True, player_color)
        
        self.screen.blit(turn_surface, (10, 10))
        self.screen.blit(player_surface, (10, 40))
        
        # Draw scores
        score_y = 70
        for player in self.game_state.players:
            color = self.player_colors[player.id % len(self.player_colors)]
            score_text = f"Player {player.id + 1}: {player.score} pts"
            score_surface = self.font.render(score_text, True, color)
            self.screen.blit(score_surface, (10, score_y))
            score_y += 20
            
        # Draw game over indicator if applicable
        if self.game_state.game_over:
            game_over_text = "GAME OVER"
            if self.game_state.winner:
                winner_id = self.game_state.winner.id
                winner_color = self.player_colors[winner_id % len(self.player_colors)]
                winner_text = f"Player {winner_id + 1} wins!"
                
                game_over_surface = self.large_font.render(game_over_text, True, (255, 255, 255))
                winner_surface = self.large_font.render(winner_text, True, winner_color)
                
                screen_width, _ = self.screen.get_size()
                game_over_rect = game_over_surface.get_rect(center=(screen_width // 2, 30))
                winner_rect = winner_surface.get_rect(center=(screen_width // 2, 60))
                
                self.screen.blit(game_over_surface, game_over_rect)
                self.screen.blit(winner_surface, winner_rect)
                
    def _render_selected_info(self):
        """Render information about the selected position"""
        x, y = self.selected_position
        
        # Get tile information
        tile = self.game_state.board.get_tile(x, y)
        
        # Get armies at this position
        armies = self.game_state.board.get_armies_at(x, y)
        
        # Prepare info panel
        info_width = 200
        info_height = 150
        info_x = self.screen.get_width() - info_width - 10
        info_y = 10
        
        # Draw panel background
        panel_rect = pygame.Rect(info_x, info_y, info_width, info_height)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 1)
        
        # Draw position
        pos_text = f"Position: ({x}, {y})"
        pos_surface = self.font.render(pos_text, True, (255, 255, 255))
        self.screen.blit(pos_surface, (info_x + 10, info_y + 10))
        
        # Draw tile type
        tile_text = f"Terrain: {tile.type.name.capitalize()}"
        tile_surface = self.font.render(tile_text, True, (255, 255, 255))
        self.screen.blit(tile_surface, (info_x + 10, info_y + 30))
        
        # Draw armies info
        if armies:
            army_y = info_y + 50
            for i, army in enumerate(armies):
                player_color = self.player_colors[army.player_id % len(self.player_colors)]
                
                strength_text = f"Army {i+1}: {army.strength} troops"
                food_text = f"Food: {army.food}"
                general_text = "Has General" if army.has_general else "No General"
                player_text = f"Player {army.player_id + 1}"
                
                strength_surface = self.font.render(strength_text, True, player_color)
                food_surface = self.font.render(food_text, True, player_color)
                general_surface = self.font.render(general_text, True, player_color)
                player_surface = self.font.render(player_text, True, player_color)
                
                self.screen.blit(player_surface, (info_x + 10, army_y))
                self.screen.blit(strength_surface, (info_x + 10, army_y + 15))
                self.screen.blit(food_surface, (info_x + 10, army_y + 30))
                self.screen.blit(general_surface, (info_x + 10, army_y + 45))
                
                army_y += 60
        else:
            no_army_text = "No armies present"
            no_army_surface = self.font.render(no_army_text, True, (255, 255, 255))
            self.screen.blit(no_army_surface, (info_x + 10, info_y + 50))
            
    def handle_click(self, mouse_pos: Tuple[int, int]):
        """Handle mouse click on the board"""
        # Convert screen position to board coordinates
        board_x = (mouse_pos[0] - self.offset_x) // self.tile_size
        board_y = (mouse_pos[1] - self.offset_y) // self.tile_size
        
        # Check if click is on the board
        if not self.game_state.board.is_valid_position(board_x, board_y):
            return
            
        # Get current player
        current_player = self.game_state.get_current_player()
        
        # Get armies at clicked position
        armies_at_pos = self.game_state.board.get_armies_at(board_x, board_y)
        current_player_armies = [a for a in armies_at_pos if a.player_id == current_player.id]
        
        # If there's already a selection
        if self.selected_position is not None:
            selected_x, selected_y = self.selected_position
            selected_armies = self.game_state.board.get_armies_at(selected_x, selected_y)
            player_selected_armies = [a for a in selected_armies if a.player_id == current_player.id]
            
            # If we have a selected army and clicked on a valid move destination
            if player_selected_armies and (board_x, board_y) in self.highlighted_positions:
                # Try to move the army
                if selected_x == board_x and selected_y == board_y:
                    # Clicked on the same tile, deselect
                    self.selected_position = None
                    self.highlighted_positions.clear()
                else:
                    # Try to move to the new position
                    army_to_move = player_selected_armies[0]  # Just move the first army for now
                    
                    # If there are current player armies at destination, merge
                    if current_player_armies and abs(selected_x - board_x) + abs(selected_y - board_y) == 1:
                        self.game_state.merge_armies(current_player_armies[0], army_to_move)
                    else:
                        # Otherwise move
                        self.game_state.move_army(army_to_move, board_x, board_y)
                    
                    # Update selection
                    self.selected_position = (board_x, board_y)
                    self._update_movement_highlights()
            else:
                # Clicked elsewhere, update selection
                self.selected_position = (board_x, board_y) if armies_at_pos else None
                self._update_movement_highlights()
        else:
            # No current selection, select the clicked tile if it has armies
            self.selected_position = (board_x, board_y) if armies_at_pos else None
            self._update_movement_highlights()
            
    def _update_movement_highlights(self):
        """Update which tiles are highlighted for movement"""
        self.highlighted_positions.clear()
        
        if self.selected_position is None:
            return
            
        x, y = self.selected_position
        armies = self.game_state.board.get_armies_at(x, y)
        current_player = self.game_state.get_current_player()
        
        # Only highlight for current player's armies
        player_armies = [a for a in armies if a.player_id == current_player.id]
        if not player_armies:
            return
            
        # Use the first army's movement range
        army = player_armies[0]
        movement_range = self.game_state._calculate_movement_range(army)
        
        # Highlight tiles within movement range
        for dx in range(-movement_range, movement_range + 1):
            for dy in range(-movement_range, movement_range + 1):
                # Manhattan distance
                distance = abs(dx) + abs(dy)
                if 0 < distance <= movement_range:
                    highlight_x, highlight_y = x + dx, y + dy
                    if self.game_state.board.is_valid_position(highlight_x, highlight_y):
                        self.highlighted_positions.add((highlight_x, highlight_y))
                        
    def select_army(self, army: Army):
        """Select a specific army"""
        self.selected_position = (army.x, army.y)
        self._update_movement_highlights()
