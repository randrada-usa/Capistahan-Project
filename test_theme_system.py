"""
test_theme_system.py
Test theme manager and asset loading without real assets.
"""

import os
import sys
import pygame
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_assets():
    """Create a temporary assets folder structure with placeholder files."""
    temp_dir = tempfile.mkdtemp(prefix="game_test_")
    assets_dir = os.path.join(temp_dir, "assets")
    
    # Create folder structure
    themes = ['food', 'culture', 'people']
    subfolders = ['backgrounds', 'sprites', 'audio', 'ui']
    
    for theme in themes:
        for sub in subfolders:
            os.makedirs(os.path.join(assets_dir, theme, sub), exist_ok=True)
    
    # Shared folders
    for sub in ['audio', 'ui', 'sprites']:
        os.makedirs(os.path.join(assets_dir, sub), exist_ok=True)
    
    # Create dummy image files (1x1 PNG bytes)
    dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Create dummy MP3
    dummy_mp3 = b'\xff\xfb\x90\x00' + b'\x00' * 100
    
    # Themed assets
    for theme in themes:
        with open(os.path.join(assets_dir, theme, 'backgrounds', 'background.png'), 'wb') as f:
            f.write(dummy_png)
        
        for sprite in ['Sprite1.png', 'Sprite_right.png', 'Sprite_left.png', 
                       'corner_chibi.png', 'Good item.png', 'Bad item.png']:
            with open(os.path.join(assets_dir, theme, 'sprites', sprite), 'wb') as f:
                f.write(dummy_png)
        
        with open(os.path.join(assets_dir, theme, 'audio', 'In game theme.mp3'), 'wb') as f:
            f.write(dummy_mp3)
    
    # Shared assets
    for h in ['H1.png', 'H2.png', 'H3.png', 'H4.png', 'H5.png', 'H6.png']:
        with open(os.path.join(assets_dir, 'sprites', h), 'wb') as f:
            f.write(dummy_png)
    
    for btn in ['start_button.png', 'retry_button.png', 'menu_button.png', 
                'title1.png', 'title2.png']:
        with open(os.path.join(assets_dir, 'ui', btn), 'wb') as f:
            f.write(dummy_png)
    
    audio_files = ['Menu theme v3.mp3', 'Start (mp3cut.net).mp3', 
                   'Good item (mp3cut.net).mp3', 'Bad item (mp3cut.net).mp3',
                   'minus 1 (mp3cut.net).mp3', 'plus 1 (mp3cut.net).mp3',
                   'rare_catch.mp3', 'ultra_catch.mp3', 'In game theme v2.mp3']
    for aud in audio_files:
        with open(os.path.join(assets_dir, 'audio', aud), 'wb') as f:
            f.write(dummy_mp3)
    
    print(f"[Test] Created test assets in: {assets_dir}")
    return temp_dir, assets_dir

def test_theme_manager():
    """Test ThemeManager class."""
    print("\n=== TESTING THEME MANAGER ===")
    from src.game.theme_manager import ThemeManager
    
    for theme in ['food', 'culture', 'people', 'FOOD', 'Culture']:
        tm = ThemeManager(theme)
        assert tm.get_theme() == theme.lower().strip()
        print(f"✓ Theme '{theme}' -> '{tm.get_theme()}'")
    
    tm = ThemeManager('invalid_theme')
    assert tm.get_theme() == 'food'
    print("✓ Invalid theme falls back to 'food'")
    
    tm = ThemeManager('culture')
    assert tm.get_theme_display_name() == 'Capiz Traditions'
    print(f"✓ Display name: {tm.get_theme_display_name()}")

def test_asset_manager(assets_dir):
    """Test AssetManager with dummy assets."""
    print("\n=== TESTING ASSET MANAGER ===")
    
    # Monkey-patch resource_path
    import src.game.asset_manager as am
    
    def test_resource_path(relative_path):
        # Return test assets folder directly
        return assets_dir if not relative_path else os.path.join(assets_dir, relative_path)
    
    am.resource_path = lambda x: test_resource_path(x)
    
    # Initialize pygame for audio
    pygame.init()
    pygame.mixer.init()
    
    from src.game.asset_manager import AssetManager
    
    for theme in ['food', 'culture', 'people']:
        print(f"\n-- Testing theme: {theme} --")
        assets = AssetManager(theme=theme).load_all()
        
        assert assets.get('background') is not None
        assert assets.get('sprite_idle') is not None
        print(f"  ✓ Themed assets loaded")
        
        assert assets.get('h1') is not None
        assert assets.get('start_button') is not None
        print(f"  ✓ Shared assets loaded")
        
        assert assets.get_theme_manager().get_theme() == theme
        print(f"  ✓ Theme manager reports: {theme}")
        
        assert assets.music_paths.get('ingame') is not None
        print(f"  ✓ Themed music path set")

def test_game_state():
    """Test GameState with rarity scoring."""
    print("\n=== TESTING GAME STATE ===")
    from src.game.game_state import GameState
    
    gs = GameState(assets=None)
    
    class MockItem:
        def __init__(self, item_type, rarity='common'):
            self.type = item_type
            self.rarity = rarity
    
    gs.handle_caught([MockItem('good', 'common')])
    assert gs.score == 1
    print(f"✓ Common item: +1 point (score: {gs.score})")
    
    gs.handle_caught([MockItem('good', 'rare')])
    assert gs.score == 4
    print(f"✓ Rare item: +3 points (score: {gs.score})")
    
    gs.handle_caught([MockItem('good', 'ultra')])
    assert gs.score == 9
    print(f"✓ Ultra item: +5 points (score: {gs.score})")
    
    gs.reset()
    gs.update_timer(0.5)
    assert gs.time_remaining == 59.5
    print(f"✓ Timer countdown: 60 -> {gs.time_remaining}")

def main():
    """Run all tests."""
    print("=" * 50)
    print("CAPIZTAHAN THEME SYSTEM TEST")
    print("=" * 50)
    
    temp_dir = None
    try:
        temp_dir, assets_dir = create_test_assets()
        test_theme_manager()
        test_asset_manager(assets_dir)
        test_game_state()
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up: {temp_dir}")

if __name__ == "__main__":
    main()