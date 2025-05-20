"""
Serialization utilities for Strategic Conquest
"""

import json
import yaml
from typing import Dict, Any, List, Tuple
import os

from game.state import GameState
from game.board import Board, Tile, TileType
from game.army import Army


def save_game(game_state: GameState, filename: str):
    """
    Save the game state to a file
    
    Args:
        game_state: The current game state
        filename: File to save to
    """
    # Create a dictionary representing the game state
    data = {
        'turn_number': game_state.turn_number,
        'current_player_index': game_state.current_player_index,
        'game_over': game_state.game_over,
        'winner': game_state.winner.id if game_state.winner else None,
        
        'board': {
            'width': game_state.board.width,
            'height': game_state.board.height,
            'tiles': [
                [
                    {
                        'type': tile.type.name,
                        'player_id': tile.player_id
                    }
                    for tile in row
                ]
                for row in game_state.board.tiles
            ]
        },
        
        'players': [
            {
                'id': player.id,
                'name': player.name,
                'score': player.score,
                'headquarters_position': player.headquarters_position,
                'is_eliminated': player.is_eliminated,
                'armies': [
                    {
                        'x': army.x,
                        'y': army.y,
                        'strength': army.strength,
                        'food': army.food,
                        'has_general': army.has_general,
                        'moved_this_turn': army.moved_this_turn,
                        'fought_this_turn': army.fought_this_turn
                    }
                    for army in player.armies
                ]
            }
            for player in game_state.players
        ]
    }
    
    # Save to file
    with open(filename, 'w') as f:
        if filename.endswith('.json'):
            json.dump(data, f, indent=4)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            yaml.dump(data, f, default_flow_style=False)
        else:
            # Default to JSON
            json.dump(data, f, indent=4)


def load_game(filename: str) -> GameState:
    """
    Load a game state from a file
    
    Args:
        filename: File to load from
        
    Returns:
        Loaded GameState
    """
    # Load data from file
    with open(filename, 'r') as f:
        if filename.endswith('.json'):
            data = json.load(f)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            data = yaml.safe_load(f)
        else:
            # Default to JSON
            data = json.load(f)
    
    # Create a new board
    board_data = data['board']
    board = Board(board_data['width'], board_data['height'])
    
    # Clear the board
    board._initialize_board()
    
    # Set up tiles
    for y, row in enumerate(board_data['tiles']):
        for x, tile_data in enumerate(row):
            tile = board.get_tile(x, y)
            tile.type = TileType[tile_data['type']]
            tile.player_id = tile_data['player_id']
    
    # Create a new game state
    game_state = GameState(board, len(data['players']))
    
    # Overwrite game state properties
    game_state.turn_number = data['turn_number']
    game_state.current_player_index = data['current_player_index']
    game_state.game_over = data['game_over']
    
    # Clear existing players data
    game_state.players = []
    
    # Set up players
    for player_data in data['players']:
        player = game_state.players[player_data['id']]
        player.name = player_data['name']
        player.score = player_data['score']
        player.headquarters_position = tuple(player_data['headquarters_position'])
        player.is_eliminated = player_data['is_eliminated']
        
        # Clear existing armies
        player.armies = []
        
        # Create armies
        for army_data in player_data['armies']:
            army = Army(
                x=army_data['x'],
                y=army_data['y'],
                strength=army_data['strength'],
                food=army_data['food'],
                has_general=army_data['has_general'],
                player_id=player.id
            )
            army.moved_this_turn = army_data['moved_this_turn']
            army.fought_this_turn = army_data['fought_this_turn']
            
            player.armies.append(army)
            board.add_army(army)
    
    # Set winner if applicable
    winner_id = data.get('winner')
    if winner_id is not None:
        game_state.winner = game_state.players[winner_id]
    
    return game_state
