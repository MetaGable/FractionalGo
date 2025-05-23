"""
UI Controls for Strategic Conquest
Handles buttons, panels and user interaction elements
"""

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UILabel, UIHorizontalSlider, UITextBox
from typing import Dict, Tuple, List, Optional, Any

from game.state import GameState
from game.army import Army
from ui.renderer import GameRenderer


class UIControls:
    """Manages UI controls and interactions"""
    
    def __init__(self, ui_manager: pygame_gui.UIManager, game_state: GameState, renderer: GameRenderer):
        self.ui_manager = ui_manager
        self.game_state = game_state
        self.renderer = renderer
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pygame.display.get_surface().get_size()
        
        # Create UI elements
        self._create_game_controls()
        self._create_army_controls()
        
        # Split dialog state
        self.split_dialog = None
        self.split_slider = None
        self.split_food_slider = None
        self.split_general_button = None
        self.splitting_army = None
        
    def _create_game_controls(self):
        """Create main game control buttons"""
        # Create control panel
        control_panel_rect = pygame.Rect(
            10, self.screen_height - 60, 300, 50
        )
        self.control_panel = UIPanel(
            relative_rect=control_panel_rect,
            starting_layer_height=1,
            manager=self.ui_manager
        )
        
        # End Turn button
        end_turn_rect = pygame.Rect(
            10, 10, 100, 30
        )
        self.end_turn_button = UIButton(
            relative_rect=end_turn_rect,
            text="End Turn",
            manager=self.ui_manager,
            container=self.control_panel
        )
        
        # New Game button
        new_game_rect = pygame.Rect(
            120, 10, 100, 30
        )
        self.new_game_button = UIButton(
            relative_rect=new_game_rect,
            text="New Game",
            manager=self.ui_manager,
            container=self.control_panel
        )
        
    def _create_army_controls(self):
        """Create controls for army management"""
        # Create army panel
        army_panel_rect = pygame.Rect(
            self.screen_width - 310, self.screen_height - 60, 300, 50
        )
        self.army_panel = UIPanel(
            relative_rect=army_panel_rect,
            starting_layer_height=1,
            manager=self.ui_manager
        )
        
        # Split button
        split_rect = pygame.Rect(
            10, 10, 80, 30
        )
        self.split_button = UIButton(
            relative_rect=split_rect,
            text="Split",
            manager=self.ui_manager,
            container=self.army_panel
        )
        
        # Merge button
        merge_rect = pygame.Rect(
            100, 10, 80, 30
        )
        self.merge_button = UIButton(
            relative_rect=merge_rect,
            text="Merge",
            manager=self.ui_manager,
            container=self.army_panel
        )
        
        # Retreat button
        retreat_rect = pygame.Rect(
            190, 10, 80, 30
        )
        self.retreat_button = UIButton(
            relative_rect=retreat_rect,
            text="Retreat",
            manager=self.ui_manager,
            container=self.army_panel
        )
        
    def process_events(self, event: pygame.event.Event):
        """Process UI events"""
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                self._handle_button_press(event)
            elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                self._handle_slider_moved(event)
                
    def _handle_button_press(self, event: pygame.event.Event):
        """Handle button press events"""
        if event.ui_element == self.end_turn_button:
            self.game_state.next_turn()
            self.renderer.selected_position = None
            self.renderer.highlighted_positions.clear()
        elif event.ui_element == self.new_game_button:
            # Reset game
            self.game_state.board.generate_random_map()
            self.game_state._setup_game()
            self.game_state.turn_number = 1
            self.game_state.current_player_index = 0
            self.game_state.game_over = False
            self.game_state.winner = None
            self.renderer.selected_position = None
            self.renderer.highlighted_positions.clear()
        elif event.ui_element == self.split_button:
            self._show_split_dialog()
        elif event.ui_element == self.merge_button:
            self._handle_merge()
        elif event.ui_element == self.retreat_button:
            self._handle_retreat()
        elif self.split_dialog and event.ui_element == self.split_general_button:
            # Toggle general assignment in split dialog
            if self.split_general_button.text == "Keep General":
                self.split_general_button.set_text("Send General")
            else:
                self.split_general_button.set_text("Keep General")
        elif self.split_dialog and event.ui_element == self.split_confirm_button:
            self._handle_split_confirm()
        elif self.split_dialog and event.ui_element == self.split_cancel_button:
            self._close_split_dialog()
            
    def _handle_slider_moved(self, event: pygame.event.Event):
        """Handle slider movement events"""
        if self.split_dialog and event.ui_element == self.split_slider:
            # Update the labels showing split values
            if self.splitting_army:
                strength_value = int(self.split_slider.get_current_value())
                self.split_keep_label.set_text(f"Keep: {self.splitting_army.strength - strength_value}")
                self.split_new_label.set_text(f"New: {strength_value}")
                
        if self.split_dialog and event.ui_element == self.split_food_slider:
            # Update the labels showing food split values
            if self.splitting_army:
                food_value = int(self.split_food_slider.get_current_value())
                self.split_keep_food_label.set_text(f"Keep: {self.splitting_army.food - food_value}")
                self.split_new_food_label.set_text(f"New: {food_value}")
                
    def _show_split_dialog(self):
        """Show the army splitting dialog"""
        # Check if an army is selected
        if not self.renderer.selected_position:
            return
            
        x, y = self.renderer.selected_position
        armies = self.game_state.board.get_armies_at(x, y)
        current_player = self.game_state.get_current_player()
        
        # Filter for current player's armies
        player_armies = [a for a in armies if a.player_id == current_player.id]
        if not player_armies:
            return
            
        # Use the first army
        army = player_armies[0]
        self.splitting_army = army
        
        # Check if army can be split
        if not army.can_split():
            return
            
        # Create split dialog
        dialog_width = 300
        dialog_height = 300
        dialog_rect = pygame.Rect(
            (self.screen_width - dialog_width) // 2,
            (self.screen_height - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        
        self.split_dialog = UIPanel(
            relative_rect=dialog_rect,
            starting_layer_height=1,
            manager=self.ui_manager
        )
        
        # Title
        title_rect = pygame.Rect(
            10, 10, dialog_width - 20, 30
        )
        UILabel(
            relative_rect=title_rect,
            text="Split Army",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        # Strength slider
        strength_label_rect = pygame.Rect(
            10, 50, dialog_width - 20, 20
        )
        UILabel(
            relative_rect=strength_label_rect,
            text="New Army Strength",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        slider_rect = pygame.Rect(
            20, 80, dialog_width - 40, 20
        )
        self.split_slider = UIHorizontalSlider(
            relative_rect=slider_rect,
            start_value=1,
            value_range=(1, army.strength - 1),
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        # Labels for split values
        keep_label_rect = pygame.Rect(
            20, 100, (dialog_width - 40) // 2, 20
        )
        self.split_keep_label = UILabel(
            relative_rect=keep_label_rect,
            text=f"Keep: {army.strength - 1}",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        new_label_rect = pygame.Rect(
            (dialog_width - 40) // 2 + 20, 100, (dialog_width - 40) // 2, 20
        )
        self.split_new_label = UILabel(
            relative_rect=new_label_rect,
            text=f"New: 1",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        # Food slider
        food_label_rect = pygame.Rect(
            10, 130, dialog_width - 20, 20
        )
        UILabel(
            relative_rect=food_label_rect,
            text="New Army Food",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        food_slider_rect = pygame.Rect(
            20, 160, dialog_width - 40, 20
        )
        self.split_food_slider = UIHorizontalSlider(
            relative_rect=food_slider_rect,
            start_value=1,
            value_range=(1, army.food - 1),
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        # Labels for food split values
        keep_food_label_rect = pygame.Rect(
            20, 180, (dialog_width - 40) // 2, 20
        )
        self.split_keep_food_label = UILabel(
            relative_rect=keep_food_label_rect,
            text=f"Keep: {army.food - 1}",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        new_food_label_rect = pygame.Rect(
            (dialog_width - 40) // 2 + 20, 180, (dialog_width - 40) // 2, 20
        )
        self.split_new_food_label = UILabel(
            relative_rect=new_food_label_rect,
            text=f"New: 1",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        # General assignment (only if army has a general)
        if army.has_general:
            general_button_rect = pygame.Rect(
                (dialog_width - 150) // 2, 210, 150, 30
            )
            self.split_general_button = UIButton(
                relative_rect=general_button_rect,
                text="Keep General",
                manager=self.ui_manager,
                container=self.split_dialog
            )
        else:
            self.split_general_button = None
            
        # Confirm and Cancel buttons
        confirm_rect = pygame.Rect(
            20, 250, 120, 30
        )
        self.split_confirm_button = UIButton(
            relative_rect=confirm_rect,
            text="Confirm",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
        cancel_rect = pygame.Rect(
            160, 250, 120, 30
        )
        self.split_cancel_button = UIButton(
            relative_rect=cancel_rect,
            text="Cancel",
            manager=self.ui_manager,
            container=self.split_dialog
        )
        
    def _close_split_dialog(self):
        """Close the split dialog"""
        if self.split_dialog:
            self.split_dialog.kill()
            self.split_dialog = None
            self.split_slider = None
            self.split_food_slider = None
            self.split_general_button = None
            self.split_confirm_button = None
            self.split_cancel_button = None
            self.splitting_army = None
            
    def _handle_split_confirm(self):
        """Handle confirmation of army split"""
        if not self.splitting_army:
            self._close_split_dialog()
            return
            
        # Get values from sliders
        new_strength = int(self.split_slider.get_current_value())
        new_food = int(self.split_food_slider.get_current_value())
        
        # Determine general assignment
        keep_general = True
        if self.split_general_button:
            keep_general = self.split_general_button.text == "Keep General"
            
        # Find a valid adjacent position for the new army
        valid_positions = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x = self.splitting_army.x + dx
            new_y = self.splitting_army.y + dy
            
            if self.game_state.board.is_valid_position(new_x, new_y):
                valid_positions.append((new_x, new_y))
                
        if not valid_positions:
            self._close_split_dialog()
            return
            
        # For now, just use the first valid position
        new_x, new_y = valid_positions[0]
        
        # Perform the split
        new_army = self.game_state.split_army(
            self.splitting_army, new_strength, new_food, not keep_general, new_x, new_y
        )
        
        # Update selected position to the new army
        if new_army:
            self.renderer.select_army(new_army)
            
        # Close the dialog
        self._close_split_dialog()
        
    def _handle_merge(self):
        """Handle merging of armies"""
        # Check if an army is selected
        if not self.renderer.selected_position:
            return
            
        x, y = self.renderer.selected_position
        armies = self.game_state.board.get_armies_at(x, y)
        current_player = self.game_state.get_current_player()
        
        # Filter for current player's armies
        player_armies = [a for a in armies if a.player_id == current_player.id]
        if not player_armies or len(player_armies) < 2:
            return
            
        # Merge all armies into the first one
        primary_army = player_armies[0]
        for i in range(1, len(player_armies)):
            self.game_state.merge_armies(primary_army, player_armies[i])
            
        # Update selection
        self.renderer.select_army(primary_army)
        
    def _handle_retreat(self):
        """Handle army retreat"""
        # Check if an army is selected
        if not self.renderer.selected_position:
            return
            
        x, y = self.renderer.selected_position
        armies = self.game_state.board.get_armies_at(x, y)
        current_player = self.game_state.get_current_player()
        
        # Filter for current player's armies
        player_armies = [a for a in armies if a.player_id == current_player.id]
        if not player_armies:
            return
            
        # Check if army is at headquarters
        hq_x, hq_y = current_player.headquarters_position
        if x != hq_x or y != hq_y:
            return
            
        # Retreat all armies
        for army in player_armies:
            self.game_state.retreat_army(army)
            
        # Clear selection
        self.renderer.selected_position = None
        self.renderer.highlighted_positions.clear()

    def update(self, time_delta: float):
        """Update UI controls"""
        # Update button states based on game state
        self._update_button_states()
        
    def _update_button_states(self):
        """Update button states based on current game state"""
        # Disable controls if game is over
        game_over = self.game_state.game_over
        self.end_turn_button.disable() if game_over else self.end_turn_button.enable()
        
        # Get selection info
        has_selection = self.renderer.selected_position is not None
        
        if has_selection:
            x, y = self.renderer.selected_position
            armies = self.game_state.board.get_armies_at(x, y)
            current_player = self.game_state.get_current_player()
            player_armies = [a for a in armies if a.player_id == current_player.id]
            
            # Enable/disable Split button
            can_split = (len(player_armies) > 0 and 
                        player_armies[0].can_split() and 
                        len(self.game_state.board.get_adjacent_positions(x, y)) > 0)
            self.split_button.enable() if can_split and not game_over else self.split_button.disable()
            
            # Enable/disable Merge button
            can_merge = len(player_armies) > 1
            self.merge_button.enable() if can_merge and not game_over else self.merge_button.disable()
            
            # Enable/disable Retreat button
            hq_x, hq_y = current_player.headquarters_position if current_player else (-1, -1)
            can_retreat = len(player_armies) > 0 and x == hq_x and y == hq_y
            self.retreat_button.enable() if can_retreat and not game_over else self.retreat_button.disable()
        else:
            # No selection, disable all army controls
            self.split_button.disable()
            self.merge_button.disable()
            self.retreat_button.disable()
