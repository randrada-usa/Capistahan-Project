"""
main.py
Capiztahan Gacha Game - Main Entry Point
"""

import sys
import os
import pygame
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.start_screen import show_start_screen
from src.ui.wheel_screen import show_wheel_screen
from src.ui.end_screen import show_end_screen
from src.game.asset_manager import AssetManager
from src.game.theme_manager import ThemeManager
from src.game.game_loop import GameLoop

try:
    from src.cv.gesture_controller import GestureController
    CV_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] CV not available: {e}")
    CV_AVAILABLE = False


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen_w = 1920
        self.screen_h = 1080
        
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("CAPIZTAHAN GACHA - 6-byte Studios")
        
        icon_path = os.path.join(os.path.dirname(__file__), 'Icon.ico')
        if os.path.exists(icon_path):
            try:
                icon_surface = pygame.image.load(icon_path)
                pygame.display.set_icon(icon_surface)
            except Exception as e:
                print(f"[WARNING] Failed to load icon: {e}")

        # CV setup
        self.gesture_controller = None
        self.use_cv = False
        self.debug_window = True
        self.camera_profile = os.environ.get('CAMERA_PROFILE', 'high_angle')
        print(f"[Game] Camera profile: {self.camera_profile}")

        if CV_AVAILABLE:
            cv2.namedWindow("GAMEFRICKS PROTOTYPE01 - Camera Feed", cv2.WINDOW_NORMAL)
            
        self.init_cv()
        
        # Theme/Assets set after wheel
        self.theme_manager = None
        self.assets = None
        self.running = True
    
    def init_cv(self):
        """Initialize Gesture Controller."""
        if CV_AVAILABLE:
            try:
                self.gesture_controller = GestureController(
                    camera_profile=self.camera_profile
                ).start()
                self.use_cv = True
                print(f"[Game] CV active with '{self.camera_profile}' profile")
            except Exception as e:
                print(f"[Game] CV failed: {e}")
                import traceback
                traceback.print_exc()
                self.use_cv = False

    def run(self):
        """Main game flow."""
        try:
            while self.running:
                # 1. START SCREEN
                print("[Game] Showing start screen...")
                result, start_screen_snapshot = show_start_screen(
                    self.screen, 
                    self.screen_w, 
                    self.screen_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None
                )
                
                if not result:
                    print("[Game] User quit from start screen")
                    break
                
                # 2. WHEEL SCREEN
                print("[Game] Showing wheel screen...")
                selected_theme = show_wheel_screen(
                    self.screen,
                    self.screen_w,
                    self.screen_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None,
                    assets=None,  # No assets yet, wheel uses its own
                    background=start_screen_snapshot  # Captured start screen behind wheel
                )
                
                if selected_theme is None:
                    print("[Game] User quit from wheel")
                    break
                
                print(f"[Game] Selected theme: {selected_theme}")
                
                # 3. LOAD ASSETS (NOW loads food_bg.png, etc.)
                try:
                    self.theme_manager = ThemeManager(selected_theme)
                    self.assets = AssetManager(selected_theme).load_all()
                except Exception as e:
                    print(f"[Game] Error loading assets: {e}")
                    continue
                
                # 4. GAMEPLAY LOOP
                print("[Game] Starting gameplay loop...")
                game_loop = GameLoop(
                    screen=self.screen,
                    assets=self.assets,
                    theme_manager=self.theme_manager,
                    gesture_controller=self.gesture_controller,
                    use_cv=self.use_cv
                )
                
                # THIS RUNS THE ACTUAL GAME
                game_result = game_loop.run()
                
                if not game_result['continue']:
                    print("[Game] User quit during gameplay")
                    break
                
                print(f"[Game] Game over! Score: {game_result['game_state'].score}")
                
                # 5. END SCREEN
                retry = show_end_screen(
                    self.screen,
                    game_result['game_state'],
                    background_snapshot=game_result['snapshot'],
                    screen_width=self.screen_w,
                    screen_height=self.screen_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None
                )
                
                if retry:
                    print("[Game] Player chose retry - going to wheel")
                    continue  # Go back to wheel
                else:
                    print("[Game] Player chose menu - going to start")
                    continue  # Go back to start screen
                    
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Safely shut down."""
        if self.gesture_controller:
            self.gesture_controller.stop()
        cv2.destroyAllWindows()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()