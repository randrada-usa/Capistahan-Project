"""
test_full_flow.py
Complete integration test for Capiztahan Gacha flow
Tests: Start → Wheel → Game (with expressions) → End
"""

import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.wheel_screen import WheelScreen, Category
from src.game.player import Player, Expression
from src.game.game_state import GameState, Rarity


def test_wheel_screen():
    """Test wheel screen functionality"""
    print("\n=== Testing Wheel Screen ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    wheel = WheelScreen(800, 600)
    wheel.start()
    
    # Simulate 6 seconds of spin
    start_time = pygame.time.get_ticks()
    test_passed = False
    
    while True:
        dt = clock.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
        wheel.update(dt)
        
        # Check if selection is valid after spin
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed > 6000:  # After 6 seconds
            if wheel.selected_category in [Category.FOOD, Category.CULTURE, Category.PEOPLE]:
                print(f"✓ Wheel selected: {wheel.selected_category.value}")
                test_passed = True
            break
        
        wheel.draw(screen)
        pygame.display.flip()
    
    pygame.quit()
    return test_passed


def test_player_expressions():
    """Test player expression system"""
    print("\n=== Testing Player Expressions ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    player = Player(800, 600)
    
    # Test 1: excited
    player.set_expression('excited', duration=0.5)
    assert player.current_expression == Expression.EXCITED, "Failed to set excited"
    print("✓ Set expression: excited")
    
    # Reset for next test
    player.current_expression = Expression.NEUTRAL
    player.expression_timer = 0
    
    # Test 2: super_excited
    player.set_expression('super_excited', duration=1.0)
    assert player.current_expression == Expression.SUPER_EXCITED, "Failed to set super_excited"
    print("✓ Set expression: super_excited")
    
    # Test 3: Auto-revert (wait for timer)
    for _ in range(70):  # 70 frames at 60fps ≈ 1.16s
        player.update(1/60)
    
    assert player.current_expression == Expression.NEUTRAL, "Expression didn't revert"
    print("✓ Expression auto-reverted to neutral")
    
    # Test 4: Particles
    player.set_expression('super_excited')
    initial_particles = len(player.particles)
    assert initial_particles > 0, "No particles spawned"
    print(f"✓ Spawned {initial_particles} particles")
    
    # Test particle update
    for _ in range(60):
        player.update(1/60)
    
    final_particles = len(player.particles)
    print(f"✓ Particles decayed to {final_particles}")
    
    # Test 5: Don't interrupt logic (super should block excited)
    player.current_expression = Expression.NEUTRAL  # Reset first
    player.set_expression('super_excited', duration=1.0)
    player.set_expression('excited', duration=0.5)  # Try to interrupt
    # Should still be super_excited because timer is still active
    assert player.current_expression == Expression.SUPER_EXCITED, "Don't-interrupt logic broken"
    print("✓ Super excited correctly blocks excited interruption")
    
    pygame.quit()
    return True


def test_game_state_events():
    """Test game state event system"""
    print("\n=== Testing Game State Events ===")
    
    gs = GameState()
    
    # Test rarity events
    gs.handle_caught_with_rarity(Rarity.ULTRA_RARE)
    events = gs.get_events_for_jen()
    assert events['ultra_rare_caught'] == True, "Ultra rare event not set"
    assert events['screen_flash'] == True, "Screen flash not triggered"
    print("✓ Ultra rare catch triggers events")
    
    gs.consume_events()
    events = gs.get_events_for_jen()
    assert all(not v for v in events.values()), "Events not cleared"
    print("✓ Events consumed properly")
    
    # Test rare catch
    gs.handle_caught_with_rarity(Rarity.RARE)
    events = gs.get_events_for_jen()
    assert events['rare_caught'] == True, "Rare event not set"
    print("✓ Rare catch triggers event")
    
    # Test scoring
    gs.reset()
    gs.handle_caught_with_rarity(Rarity.COMMON)
    assert gs.score == 10, f"Common score wrong: {gs.score}"
    
    gs.handle_caught_with_rarity(Rarity.RARE)
    assert gs.score == 60, f"Rare score wrong: {gs.score}"
    
    gs.handle_caught_with_rarity(Rarity.ULTRA_RARE)
    assert gs.score == 160, f"Ultra rare score wrong: {gs.score}"
    print("✓ Scoring system correct")
    
    # Test rarity weights
    gs.reset()
    rarity_counts = {Rarity.COMMON: 0, Rarity.RARE: 0, Rarity.ULTRA_RARE: 0}
    for _ in range(1000):
        r = gs.get_random_rarity()
        rarity_counts[r] += 1
    
    print(f"✓ Rarity distribution (1000 rolls):")
    print(f"  Common: {rarity_counts[Rarity.COMMON]} ({rarity_counts[Rarity.COMMON]/10:.1f}%)")
    print(f"  Rare: {rarity_counts[Rarity.RARE]} ({rarity_counts[Rarity.RARE]/10:.1f}%)")
    print(f"  Ultra Rare: {rarity_counts[Rarity.ULTRA_RARE]} ({rarity_counts[Rarity.ULTRA_RARE]/10:.1f}%)")
    
    # Verify rough distribution
    assert rarity_counts[Rarity.COMMON] > 600, "Common rate too low"
    assert rarity_counts[Rarity.RARE] > 150, "Rare rate too low"
    print("✓ Rarity distribution within expected ranges")
    
    return True


def test_integration_bridge():
    """Test the main.py integration bridge"""
    print("\n=== Testing Integration Bridge ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Simulate what main.py does
    def process_events(player, game_state):
        events = game_state.get_events_for_jen()
        
        if events.get('ultra_rare_caught'):
            player.set_expression('super_excited', duration=1.0)
        elif events.get('rare_caught'):
            player.set_expression('excited', duration=0.5)
        elif events.get('missed'):
            player.set_expression('sad', duration=0.5)
        
        game_state.consume_events()
    
    # Test 1: ultra rare → super excited
    player = Player(800, 600)
    gs = GameState()
    
    gs.handle_caught_with_rarity(Rarity.ULTRA_RARE)
    process_events(player, gs)
    assert player.current_expression == Expression.SUPER_EXCITED, "Bridge failed for ultra rare"
    print("✓ Bridge: ultra_rare → super_excited")
    
    # Test 2: rare → excited (need fresh player because super excited blocks excited)
    player2 = Player(800, 600)
    gs2 = GameState()
    
    gs2.handle_caught_with_rarity(Rarity.RARE)
    process_events(player2, gs2)
    assert player2.current_expression == Expression.EXCITED, "Bridge failed for rare"
    print("✓ Bridge: rare → excited")
    
    # Test 3: miss → sad (need fresh player)
    player3 = Player(800, 600)
    gs3 = GameState()
    
    gs3.handle_missed_good(1)
    process_events(player3, gs3)
    assert player3.current_expression == Expression.SAD, "Bridge failed for miss"
    print("✓ Bridge: missed → sad")
    
    # Test 4: Priority test (ultra rare wins over rare)
    player4 = Player(800, 600)
    gs4 = GameState()
    
    # Simulate both happening (shouldn't occur in game, but testing priority)
    gs4.handle_caught_with_rarity(Rarity.ULTRA_RARE)
    # Manually trigger rare too
    gs4._events['rare_caught'] = True
    
    process_events(player4, gs4)
    # Should be super_excited because ultra_rare is checked first
    assert player4.current_expression == Expression.SUPER_EXCITED, "Priority failed"
    print("✓ Bridge: ultra_rare has priority over rare")
    
    pygame.quit()
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("CAPIZTAHAN GACHA - FULL INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("Wheel Screen", test_wheel_screen),
        ("Player Expressions", test_player_expressions),
        ("Game State Events", test_game_state_events),
        ("Integration Bridge", test_integration_bridge),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} FAILED: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Ready to push.")
    else:
        print("❌ SOME TESTS FAILED. Check errors above.")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)