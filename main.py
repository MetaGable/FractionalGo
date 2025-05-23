#!/usr/bin/env python3
"""
Strategic Conquest - A territorial wargame with dynamic armies
Main entry point and game loop
"""

import os
import sys
import pygame
import pygame_gui
from pygame.locals import *

# Import game modules
from game.state import GameState
from game.board import Board
from ui.renderer import GameRenderer
from ui.controls import UIControls

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TITLE = "Strategic Conquest"


def main():
    """Main function to run the game"""
    # Setup display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Initialize game components
    board = Board(width=20, height=20)
    game_state = GameState(board=board, num_players=2)
    
    # Initialize UI
    ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
    renderer = GameRenderer(screen, game_state)
    ui_controls = UIControls(ui_manager, game_state, renderer)
    
    # Main game loop
    running = True
    while running:
        time_delta = clock.tick(FPS) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            # Pass events to UI manager
            ui_manager.process_events(event)
            
            # Pass events to UI controls
            ui_controls.process_events(event)
            
            # Handle game-specific events
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    renderer.handle_click(event.pos)
        
        # Update game state if needed (for animations, AI turns, etc.)
        game_state.update()
        
        # Update UI
        ui_manager.update(time_delta)
        
        # Render everything
        screen.fill((0, 0, 0))  # Clear screen
        renderer.render()  # Draw game elements
        ui_manager.draw_ui(screen)  # Draw UI elements
        
        pygame.display.flip()  # Update display
    
    # Clean up
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
