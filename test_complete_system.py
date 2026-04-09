# test_gio_system.py (project root)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock pygame
class MockPygame:
    class Rect:
        def __init__(self, *args): pass
        def colliderect(self, other): return False
    @staticmethod
    def transform_rotate(*args): 
        class MockSurface:
            def get_rect(self, **kwargs): return MockPygame.Rect()
        return MockSurface()

sys.modules['pygame'] = MockPygame()

from src.game.theme_manager import ThemeManager
from src.game.falling_objects import ObjectManager
from src.game.game_state import GameState
from src.game.wish_system import make_wish

print("=" * 60)
print("GIO'S GACHA SYSTEM - ALL 3 CATEGORIES TEST")
print("=" * 60)

# Test ALL three categories
CATEGORIES = ['food', 'culture', 'people']

for category in CATEGORIES:
    print(f"\n{'='*20} {category.upper()} {'='*20}")
    
    tm = ThemeManager(category)
    print(f"Theme: {tm.get_theme()}")
    print(f"Display Name: {tm.get_theme_display_name()}")
    
    om = ObjectManager(1920, theme_manager=tm)
    print(f"ObjectManager Category: {om.category}")
    
    gs = GameState(theme_manager=tm)
    print(f"Score Multiplier: {gs.multiplier}x")
    print(f"Wish Threshold: {gs.WISH_THRESHOLD} pts")
    
    # Test wish with eligible score
    result = make_wish(200, category)
    print(f"Wish Result: {'WON' if result.get('won') else 'LOSS'}")
    if result.get('won'):
        print(f"  Prize: {result['prize_name']}")
        print(f"  Code: {result['code']}")
    else:
        print(f"  Message: {result['message'][:50]}...")

print("\n" + "=" * 60)
print("ALL CATEGORIES TESTED")
print("=" * 60)