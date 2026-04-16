"""
main.py
Capiztahan Gacha Game - Main Entry Point (RESIZABLE VERSION)
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


def scale_and_flip(virtual_surface):
    """
    Scale virtual 1920x1080 surface to fit actual window while maintaining 16:9 aspect ratio.
    """
    actual_surface = pygame.display.get_surface()
    if actual_surface is None:
        pygame.display.flip()
        return
    
    actual_w, actual_h = actual_surface.get_size()
    virtual_w, virtual_h = 1920, 1080
    
    # Calculate scale to fit while maintaining aspect ratio
    scale = min(actual_w / virtual_w, actual_h / virtual_h)
    new_w = int(virtual_w * scale)
    new_h = int(virtual_h * scale)
    
    # Center on screen
    x = (actual_w - new_w) // 2
    y = (actual_h - new_h) // 2
    
    # Scale using smoothscale for better quality
    if (new_w, new_h) != (virtual_w, virtual_h):
        scaled = pygame.transform.smoothscale(virtual_surface, (new_w, new_h))
    else:
        scaled = virtual_surface
    
    # Fill with black
    actual_surface.fill((0, 0, 0))
    actual_surface.blit(scaled, (x, y))
    pygame.display.flip()


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # Virtual resolution (internal game coordinates - ALWAYS 1920x1080)
        self.virtual_w = 1920
        self.virtual_h = 1080
        
        # Start with a smaller window so user can resize (1280x720 is good for 2560x1600)
        initial_window_w = 1280
        initial_window_h = 720
        
        print(f"[DEBUG] Creating window at {initial_window_w}x{initial_window_h} (resizable)")
        print(f"[DEBUG] Internal resolution: {self.virtual_w}x{self.virtual_h} (fixed)")
        
        self.screen = pygame.display.set_mode(
            (initial_window_w, initial_window_h), 
            pygame.RESIZABLE
        )
        pygame.display.set_caption("CAPIZTAHAN GACHA - Drag edges to resize!")
        
        # Virtual surface - everything renders here at 1920x1080
        self.virtual_screen = pygame.Surface((self.virtual_w, self.virtual_h))
        
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
        self.camera_profile = os.environ.get('CAMERA_PROFILE', 'high_angle')
        print(f"[Game] Camera profile: {self.camera_profile}")

        if CV_AVAILABLE:
            cv2.namedWindow("GAMEFRICKS PROTOTYPE01 - Camera Feed", cv2.WINDOW_NORMAL)
            
        self.init_cv()
        
        # Theme/Assets set after wheel
        self.theme_manager = None
        self.assets = None
        self.running = True
        
        # Load wheel assets once (shared across all screens)
        print("[Game] Loading wheel assets...")
        self.wheel_assets = AssetManager().load_all()
        
        # === PLAY MENU MUSIC AT START ===
        self.wheel_assets.play_music('menu')
    
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
                # Handle global quit/resize
                for event in pygame.event.get([pygame.QUIT, pygame.VIDEORESIZE]):
                    if event.type == pygame.QUIT:
                        print("[DEBUG] Global QUIT event")
                        return
                    elif event.type == pygame.VIDEORESIZE:
                        print(f"[DEBUG] Resize to {event.w}x{event.h}")
                        self.screen = pygame.display.set_mode(
                            (event.w, event.h), 
                            pygame.RESIZABLE
                        )
                
                # 1. START SCREEN
                print("[Game] Showing start screen...")
                result, start_screen_snapshot = show_start_screen(
                    self.virtual_screen,
                    self.virtual_w, 
                    self.virtual_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None,
                    scale_func=scale_and_flip
                )
                
                if not result:
                    print("[Game] User quit from start screen")
                    break
                
                # 2. WHEEL SCREEN
                print("[Game] Showing wheel screen...")
                selected_theme = show_wheel_screen(
                    self.virtual_screen,
                    self.virtual_w,
                    self.virtual_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None,
                    assets=self.wheel_assets,
                    background=start_screen_snapshot,
                    scale_func=scale_and_flip
                )
                
                if selected_theme is None:
                    print("[Game] User quit from wheel")
                    break
                
                print(f"[Game] Selected theme: {selected_theme}")
                
                # 3. LOAD THEME-SPECIFIC ASSETS
                try:
                    self.theme_manager = ThemeManager(selected_theme)
                    self.assets = AssetManager(selected_theme).load_all()
                except Exception as e:
                    print(f"[Game] Error loading assets: {e}")
                    continue
                
                # === PLAY THEME-SPECIFIC GAME MUSIC ===
                self.assets.play_music('ingame')
                
                # 4. GAMEPLAY LOOP
                print("[Game] Starting gameplay loop...")
                game_loop = GameLoop(
                    screen=self.virtual_screen,
                    assets=self.assets,
                    theme_manager=self.theme_manager,
                    gesture_controller=self.gesture_controller,
                    use_cv=self.use_cv,
                    scale_func=scale_and_flip
                )
                
                game_result = game_loop.run()
                
                print(f"[DEBUG] Game loop result: continue={game_result['continue']}")
                
                if not game_result['continue']:
                    print("[Game] User quit during gameplay")
                    break
                
                print(f"[Game] Game over! Score: {game_result['game_state'].score}")
                
                # 5. END SCREEN
                retry = show_end_screen(
                    self.virtual_screen,
                    game_result['game_state'],
                    background_snapshot=game_result['snapshot'],
                    screen_width=self.virtual_w,
                    screen_height=self.virtual_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None,
                    scale_func=scale_and_flip
                )
                
                if retry:
                    print("[Game] Player chose retry - going to wheel")
                    self.wheel_assets.play_music('menu')
                    continue
                else:
                    print("[Game] Player chose menu - going to start")
                    self.wheel_assets.play_music('menu')
                    continue
                    
        except Exception as e:
            print(f"[DEBUG] ERROR: {e}")
            import traceback
            traceback.print_exc()
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