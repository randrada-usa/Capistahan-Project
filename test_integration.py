# test_integration.py
import pygame
from src.game.game_state import GameState, Rarity
from src.game.player import Player, Expression

def test_events():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Test GameState events
    gs = GameState()
    gs.handle_caught_with_rarity(Rarity.ULTRA_RARE)
    
    events = gs.get_events_for_jen()
    assert events['ultra_rare_caught'] == True
    print("✓ GameState events working")
    
    # Test Player expressions
    player = Player(800, 600)
    player.set_expression(Expression.SUPER_EXCITED, duration=1.0)
    assert player.current_expression == Expression.SUPER_EXCITED
    print("✓ Player expressions working")
    
    print("\nAll integration tests passed!")

if __name__ == "__main__":
    test_events()