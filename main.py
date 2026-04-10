"""
main.py - MODIFIED FOR CAPIZTAHAN
Added: Wheel screen integration
Flow: Start → Wheel → Game → End
"""

import sys
import os
import pygame
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.start_screen import show_start_screen
from src.ui.end_screen import show_end_screen
from src.ui.wheel_screen import show_wheel_screen
from src.game.theme_manager import ThemeManager
from src.game.asset_manager import AssetManager
from src.game.player import Player
from src.game.falling_objects import ObjectManager
from src.game.game_state import GameState

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
        self.fps = 60
        
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("CAPIZTAHAN GACHA - 6byte Studios")
        self.clock = pygame.time.Clock()
        
        icon_path = os.path.join(os.path.dirname(__file__), 'Icon.ico')
        if os.path.exists(icon_path):
            try:
                icon_surface = pygame.image.load(icon_path)
                pygame.display.set_icon(icon_surface)
            except Exception as e:
                print(f"[WARNING] Failed to load icon: {e}")

        print("Loading assets...")
        self.assets = AssetManager(theme='food').load_all()
        
        self.gesture_controller = None
        self.use_cv = False
        self.debug_window = True
        
        self.font_large = pygame.font.Font(None, 74)
        self.font_small = pygame.font.Font(None, 36)
        
        self.hand_lost_timer = 0
        self.running = True
        self.current_category = None
        self.camera_profile = os.environ.get('CAMERA_PROFILE', 'high_angle')
        print(f"[Game] Camera profile: {self.camera_profile}")

        if CV_AVAILABLE:
            cv2.namedWindow("GAMEFRICKS PROTOTYPE01 - Camera Feed", cv2.WINDOW_NORMAL)
            
        self.init_cv()

    def reset_game(self, category=None):
        self.game_duration = 60.0
        self.time_remaining = self.game_duration
        
        if category and category != self.assets.get_theme_manager().get_theme():
            print(f"[Game] Switching theme to: {category}")
            self.assets.change_theme(category)
            self.current_category = category
        
        theme_manager = self.assets.get_theme_manager()
        self.player = Player(self.screen_w, self.screen_h, self.assets)
        
        self.object_manager = ObjectManager(
            screen_width=self.screen_w,
            asset_manager=self.assets,
            theme_manager=theme_manager
        )
        
        self.game_state = GameState(
            assets=self.assets,
            theme_manager=theme_manager
        )
        
        self.hand_lost_timer = 0
        
        if self.gesture_controller:
            self.gesture_controller.reset()
        
        theme_music = self.assets.music_paths.get('ingame')
        if theme_music and os.path.exists(theme_music):
            try:
                pygame.mixer.music.load(theme_music)
                pygame.mixer.music.play(-1, fade_ms=2000)
            except Exception as e:
                print(f"[WARNING] Could not play ingame music: {e}")

    def init_cv(self):
        if CV_AVAILABLE and not self.gesture_controller:
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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
                if event.key == pygame.K_d:
                    self.debug_window = not self.debug_window
                    if not self.debug_window:
                        cv2.destroyWindow("GAMEFRICKS PROTOTYPE01 - Camera Feed")
                    else:
                        cv2.namedWindow("GAMEFRICKS PROTOTYPE01 - Camera Feed", cv2.WINDOW_NORMAL)
        return True

    def update(self, dt):
        if self.game_state.game_over:
            return None, None
        
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0
            self.game_state.trigger_game_over()
        
        player_x = None
        if self.use_cv and self.gesture_controller:
            player_x = self.gesture_controller.update()
            if player_x is None:
                self.hand_lost_timer += dt
            else:
                self.hand_lost_timer = max(0, self.hand_lost_timer - dt * 2)
        else:
            player_x, _ = pygame.mouse.get_pos()

        self.player.set_target_x(player_x)
        self.player.update(dt)
        self.object_manager.update(dt, self.game_state.score)
        caught, missed_good = self.object_manager.check_collisions(self.player.get_hitbox())
        self.game_state.handle_caught(caught)
        self.game_state.handle_missed_good(missed_good)
        self.game_state.check_game_over()
        self._process_jen_events()
        
        return player_x, self.player.y
    
    def _process_jen_events(self):
        events = self.game_state.get_events_for_jen()
        
        if events.get('ultra_rare_caught'):
            self.player.set_expression('super_excited', duration=1.0)
        elif events.get('rare_caught'):
            self.player.set_expression('excited', duration=0.5)
        elif events.get('missed'):
            self.player.set_expression('sad', duration=0.5)
        
        self.game_state.consume_events()

    def render(self, player_x, player_y):
        bg = self.assets.get('background')
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill((30, 30, 40))
        
        self.object_manager.render(self.screen)
        self.player.render(self.screen)
        
        corner_chibi = self.assets.get('corner_chibi')
        if corner_chibi:
            chibi_rect = corner_chibi.get_rect(bottomright=(self.screen_w - 20, self.screen_h - 20))
            self.screen.blit(corner_chibi, chibi_rect)
        
        self._draw_hud()

        BORDER_WIDTH = 195
        border_color = (40, 20, 10)
        pygame.draw.rect(self.screen, border_color, (0, 0, BORDER_WIDTH, self.screen_h))
        pygame.draw.rect(self.screen, border_color, (self.screen_w - BORDER_WIDTH, 0, BORDER_WIDTH, self.screen_h))

        pygame.display.flip()
        self._update_cv_window()

    def _update_cv_window(self):
        if self.debug_window and self.use_cv and self.gesture_controller:
            debug_frame = self.gesture_controller.get_debug_frame()
            if debug_frame is not None:
                cv2.imshow("GAMEFRICKS PROTOTYPE01 - Camera Feed", debug_frame)
                cv2.waitKey(1)

    def _draw_hud(self):
        score_text = self.font_large.render(f"Score: {self.game_state.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.screen_w - 550, 80))
        
        timer_color = (255, 255, 255) if self.time_remaining > 10 else (255, 50, 50)
        timer_text = self.font_large.render(f"{int(self.time_remaining)}", True, timer_color)
        timer_rect = timer_text.get_rect(center=(self.screen_w // 2, 80))
        self.screen.blit(timer_text, timer_rect)
        
        high_text = self.font_small.render(f"Best: {self.game_state.high_score}", True, (150, 75, 0))
        self.screen.blit(high_text, (self.screen_w - 550, 135))
        
        hp_index = max(1, min(6, self.game_state.lives))
        health_sprite = self.assets.get(f'h{hp_index}')
        if health_sprite:
            self.screen.blit(health_sprite, (230, 80))

        if self.current_category:
            cat_text = self.font_small.render(f"Theme: {self.current_category.upper()}", True, (255, 215, 0))
            self.screen.blit(cat_text, (230, 150))

        if self.hand_lost_timer > 0.1:
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                warning = self.font_large.render("! HAND LOST !", True, (255, 50, 50))
                self.screen.blit(warning, warning.get_rect(center=(self.screen_w // 2, 150)))

    def run(self):
        try:
            while self.running:
                # Start Screen - now returns tuple (should_continue, snapshot)
                result, start_screen_snapshot = show_start_screen(
                    self.screen,
                    self.screen_w,
                    self.screen_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None
                )

                if not result:
                    self.running = False
                    break

                # WHEEL SCREEN - Category selection with captured background
                selected_category = show_wheel_screen(
                    self.screen,
                    self.screen_w,
                    self.screen_h,
                    gesture_controller=self.gesture_controller if self.use_cv else None,
                    assets=self.assets,
                    background=start_screen_snapshot  # Now properly captured before fade
                )

                if selected_category is None:
                    continue

                print(f"[Game] Selected category: {selected_category}")

                # Gameplay with selected category
                self.reset_game(category=selected_category)
                game_active = True

                while game_active and self.running:
                    dt = self.clock.tick(self.fps) / 1000.0

                    if not self.handle_events():
                        break

                    p_x, p_y = self.update(dt)
                    self.render(p_x, p_y)

                    if self.game_state.game_over:
                        game_active = False

                # End Screen
                if self.running:
                    pygame.mixer.music.fadeout(1000)
                    snapshot = self.screen.copy()

                    retry = show_end_screen(
                        self.screen,
                        self.game_state,
                        snapshot,
                        self.screen_w,
                        self.screen_h,
                        gesture_controller=self.gesture_controller if self.use_cv else None
                    )

                    if not retry:
                        pass

        finally:
            self.cleanup()

    def cleanup(self):
        if self.gesture_controller:
            self.gesture_controller.stop()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()