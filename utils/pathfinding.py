"""
Pathfinding utilities for Strategic Conquest
"""

import heapq
from typing import List, Dict, Tuple, Set, Optional, Callable
import networkx as nx

from game.board import Board, TileType


def calculate_movement_range(board: Board, start_x: int, start_y: int, 
                            movement_points: int, 
                            player_id: Optional[int] = None) -> Set[Tuple[int, int]]:
    """
    Calculate all tiles that can be reached within a given movement range
    
    Args:
        board: The game board
        start_x, start_y: Starting position
        movement_points: Maximum movement points available
        player_id: Player ID for visibility calculations (optional)
        
    Returns:
        Set of (x, y) positions that can be reached
    """
    # Initialize data structures
    reachable = set()
    visited = set()
    queue = [(0, start_x, start_y)]  # (cost, x, y)
    
    while queue:
        cost, x, y = heapq.heappop(queue)
        
        # Skip if already visited or out of range
        if (x, y) in visited or cost > movement_points:
            continue
            
        # Mark as visited and reachable
        visited.add((x, y))
        if (x, y) != (start_x, start_y):
            reachable.add((x, y))
            
        # Check adjacent tiles
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            
            if not board.is_valid_position(nx, ny):
                continue
                
            # Skip if already visited
            if (nx, ny) in visited:
                continue
                
            # Calculate movement cost
            tile = board.get_tile(nx, ny)
            movement_cost = get_movement_cost(tile.type)
            
            # Add to queue if within range
            if cost + movement_cost <= movement_points:
                heapq.heappush(queue, (cost + movement_cost, nx, ny))
                
    return reachable


def get_movement_cost(tile_type: TileType) -> float:
    """Get movement cost for a tile type"""
    if tile_type == TileType.PLAIN or tile_type == TileType.HEADQUARTERS or tile_type == TileType.FORT:
        return 1.0
    elif tile_type == TileType.FOREST or tile_type == TileType.RIVER or tile_type == TileType.MOUNTAIN:
        return 2.0
    elif tile_type == TileType.VALLEY:
        return 1.0
    else:
        return 1.0


def find_supply_chain(board: Board, start_x: int, start_y: int, 
                      destination_x: int, destination_y: int,
                      player_id: int) -> bool:
    """
    Check if there's a supply chain from start to destination
    
    Args:
        board: The game board
        start_x, start_y: Starting position (usually HQ)
        destination_x, destination_y: Destination position
        player_id: ID of the player whose units to consider
        
    Returns:
        True if a supply chain exists, False otherwise
    """
    # Create a graph where nodes are positions with friendly armies
    G = nx.Graph()
    
    # Add nodes for all positions with friendly armies
    for pos, armies in board.armies_by_position.items():
        x, y = pos
        friendly_armies = [a for a in armies if a.player_id == player_id]
        if friendly_armies:
            G.add_node(pos)
            
    # Add edges between adjacent positions
    for pos in G.nodes:
        x, y = pos
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            adj_pos = (nx, ny)
            
            if adj_pos in G:
                G.add_edge(pos, adj_pos)
                
    # Check if start and destination are in the graph
    start_pos = (start_x, start_y)
    dest_pos = (destination_x, destination_y)
    
    if start_pos not in G or dest_pos not in G:
        return False
        
    # Check if there's a path from start to destination
    try:
        path = nx.shortest_path(G, start_pos, dest_pos)
        return len(path) > 0
    except nx.NetworkXNoPath:
        return False
