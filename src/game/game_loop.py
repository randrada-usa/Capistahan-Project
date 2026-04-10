import pygame
import sys
import cv2
import random
from src.game.player import Player
from src.game.falling_objects import ObjectManager, Rarity
from src.game.game_state import GameState


class CornerChibi:
    """Perla character that reacts to catches."""
    
    def __init__(self, asset_manager, x=150, y=20):
        self.assets = asset_manager
        self.x = x
        self.y = y
        self.current_expression = 'default'
        self.expression_timer = 0
        self.expression_duration = 2.0
        
        self.priority = {
            'default': 0,
            'happy': 1,
            'sad': 2,
            'excited': 3
        }
        
        self.bounce_offset = 0
        self.bounce_velocity = 0
        self.is_bouncing = False
        self.blink_timer = 0
        self.is_blinking = False
        self.next_blink = 2.0
        
    def set_expression(self, expression, duration=2.0):
        current_priority = self.priority.get(self.current_expression, 0)
        new_priority = self.priority.get(expression, 0)
        
        if new_priority < current_priority and self.expression_timer > 0:
            return
        
        self.current_expression = expression
        self.expression_duration = duration
        self.expression_timer = duration
        
        if expression != 'default':
            self.is_bouncing = True
            self.bounce_velocity = -10
    
    def react_to_catch(self, item):
        if item.type == 'bad':
            self.set_expression('sad', 1.5)
        elif item.rarity == Rarity.ULTRA_RARE:
            self.set_expression('excited', 3.0)
        elif item.rarity == Rarity.RARE:
            self.set_expression('happy', 2.0)
        else:
            self.set_expression('happy', 1.0)
    
    def update(self, dt):
        if self.expression_timer > 0:
            self.expression_timer -= dt
            if self.expression_timer <= 0:
                self.current_expression = 'default'
                self.is_bouncing = False
                self.bounce_offset = 0
        
        if self.is_bouncing:
            self.bounce_offset += self.bounce_velocity
            self.bounce_velocity += 30 * dt
            
            if self.bounce_offset > 0:
                self.bounce_offset = 0
                self.bounce_velocity = 0
                self.is_bouncing = False
        
        self.blink_timer += dt
        if self.blink_timer >= self.next_blink:
            self.is_blinking = True
            if self.blink_timer >= self.next_blink + 0.15:
                self.is_blinking = False
                self.blink_timer = 0
                self.next_blink = random.uniform(2.0, 4.0)
    
    def render(self, screen):
        sprite_key = f'perla_{self.current_expression}'
        sprite = self.assets.get(sprite_key)
        
        if not sprite:
            sprite = self.assets.get('perla_default')
        
        if sprite:
            draw_y = self.y + self.bounce_offset
            
            if self.current_expression != 'default':
                indicators = {'happy': '♪', 'sad': '...', 'excited': '★'}
                if self.current_expression in indicators:
                    font = pygame.font.Font(None, 48)
                    indicator = font.render(indicators[self.current_expression], True, (255, 215, 0))
                    screen.blit(indicator, (self.x + 60, int(draw_y - 20)))
            
            if self.is_blinking:
                dark_sprite = sprite.copy()
                dark_sprite.fill((0, 0, 0, 50), special_flags=pygame.BLEND_RGBA_SUB)
                screen.blit(dark_sprite, (self.x, int(draw_y)))
            else:
                screen.blit(sprite, (self.x, int(draw_y)))


class GameLoop:
    """Main gameplay loop with NON-BLOCKING camera handling."""
    
    def __init__(self, screen, assets, theme_manager, gesture_controller=None, use_cv=False):
        self.screen = screen
        self.assets = assets
        self.theme_manager = theme_manager
        self.gesture_controller = gesture_controller
        self.use_cv = use_cv and gesture_controller is not None
        
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        
        self.player = Player(self.screen_w, self.screen_h, assets)
        self.object_manager = ObjectManager(self.screen_w, assets, theme_manager)
        self.game_state = GameState(assets, theme_manager)
        
        # PERLA at top-left
        self.corner_chibi = CornerChibi(assets, x=200, y=100)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.hand_lost_timer = 0
        
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)

        # Track whether we've created the OpenCV window ourselves,
        # so we never call imshow if the gesture controller already does.
        self._cv_window_name = "CAPIZTAHAN - Camera Feed"
        self._cv_window_created = False
        
        print(f"[GameLoop] Ready - Theme: {theme_manager.get_theme()}, CV: {self.use_cv}")
    
    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Run gameplay until game over or quit."""
        print("[GameLoop] Starting game loop...")
        
        while not self.game_state.game_over and self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # CRITICAL: Always pump pygame events to prevent "Not Responding"
            pygame.event.pump()
            
            if not self.handle_events():
                self._close_cv_window()
                return {'continue': False, 'game_state': None, 'snapshot': None}
            
            self.update(dt)
            self.render()
        
        print(f"[GameLoop] Game ended. Score: {self.game_state.score}")
        self._close_cv_window()
        return {
            'continue': True,
            'game_state': self.game_state,
            'snapshot': self.screen.copy()
        }

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
            
            if not self.use_cv and event.type == pygame.MOUSEMOTION:
                mouse_x, _ = pygame.mouse.get_pos()
                self.player.set_target_x(mouse_x)
        
        return True

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        """Update game logic."""
        if self.use_cv and self.gesture_controller:
            try:
                screen_x = self.gesture_controller.update()
                self.player.set_target_x(screen_x)
                
                if screen_x is None:
                    self.hand_lost_timer += dt
                else:
                    self.hand_lost_timer = max(0, self.hand_lost_timer - dt * 2)
            except Exception as e:
                print(f"[GameLoop] CV Error: {e}")
                self.use_cv = False  # Disable CV on error to prevent hangs
        
        self.player.update(dt)
        self.object_manager.update(dt, self.game_state.score)
        
        # Collisions
        caught, missed_good = self.object_manager.check_collisions(
            self.player.get_hitbox()
        )
        
        for item in caught:
            self.game_state.handle_caught([item])
            self.corner_chibi.react_to_catch(item)
            
            if item.rarity == Rarity.ULTRA_RARE:
                self.player.set_expression('super_excited', 1.0)
            elif item.rarity == Rarity.RARE:
                self.player.set_expression('excited', 0.5)
        
        self.game_state.handle_missed_good(missed_good)
        self.game_state.check_game_over()
        self.corner_chibi.update(dt)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self):
        """Render everything, then pump OpenCV exactly once per frame."""
        # Background
        bg = self.assets.get('background')
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill((30, 30, 40))
        
        # Game objects
        self.object_manager.render(self.screen)
        self.player.render(self.screen)
        self.corner_chibi.render(self.screen)
        
        # HUD
        self._draw_hud()
        
        # CRITICAL: Flip pygame display first so the game never stalls
        pygame.display.flip()
        
        # Camera display — one imshow + one waitKey(1), no more, no less
        if self.use_cv:
            self._update_camera_display()
            # Always call waitKey once per frame so OpenCV processes its own
            # window events.  Putting it here (outside _update_camera_display)
            # guarantees it runs even when get_debug_frame() returns None.
            try:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC in camera window — ignore, let pygame ESC handle quit
                    pass
            except Exception as e:
                print(f"[GameLoop] cv2.waitKey error: {e}")
                self.use_cv = False

    def _update_camera_display(self):
        """Push the latest debug frame to the single OpenCV window.

        Rules that prevent duplication / hangs:
        - We call cv2.imshow() here and NOWHERE else (the gesture controller
          must NOT call imshow internally; it should only return the frame).
        - waitKey(1) is called by the caller (render) so it happens exactly
          once per game frame regardless of whether a frame was available.
        """
        if not self.gesture_controller:
            return
        
        try:
            debug_frame = self.gesture_controller.get_debug_frame()
            
            if debug_frame is not None:
                # namedWindow + WINDOW_NORMAL lets the user resize without
                # creating a second window on subsequent imshow calls.
                if not self._cv_window_created:
                    cv2.namedWindow(self._cv_window_name, cv2.WINDOW_NORMAL)
                    self._cv_window_created = True
                
                cv2.imshow(self._cv_window_name, debug_frame)

        except Exception as e:
            print(f"[GameLoop] Camera display error (disabling): {e}")
            self.use_cv = False

    def _close_cv_window(self):
        """Cleanly destroy the OpenCV window when the game exits."""
        if self._cv_window_created:
            try:
                cv2.destroyWindow(self._cv_window_name)
            except Exception:
                pass
            self._cv_window_created = False

    # ------------------------------------------------------------------
    # HUD helpers
    # ------------------------------------------------------------------

    def _draw_hud(self):
        """Draw HUD."""
        # Score (top-right)
        score_text = self.font.render(f"Score: {self.game_state.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.screen_w - score_text.get_width() - 200, 100))
        
        # Category
        cat_text = self.small_font.render(
            f"{self.theme_manager.get_theme_display_name()} (x{self.game_state.multiplier})", 
            True, (255, 215, 0)
        )
        self.screen.blit(cat_text, (20, 285))
        
        # Wish progress
        if not self.game_state.is_wish_eligible():
            status = self.game_state.get_wish_status()
            bar_w = 300
            bar_h = 20
            bar_x = 20
            bar_y = 400
            
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (bar_x, bar_y, bar_w, bar_h), border_radius=10)
            fill_w = int(bar_w * (status['progress_percent'] / 100))
            pygame.draw.rect(self.screen, (255, 215, 0), 
                           (bar_x, bar_y, fill_w, bar_h), border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           (bar_x, bar_y, bar_w, bar_h), 2, border_radius=10)
            
            progress_text = self.small_font.render(
                f"Wish: {int(status['current'])}/{status['threshold']}", 
                True, (255, 255, 255)
            )
            self.screen.blit(progress_text, (bar_x, bar_y + 25))
        else:
            wish_text = self.small_font.render("★ WISH READY! ★", True, (255, 215, 0))
            self.screen.blit(wish_text, (20, 400))
        
        # Input mode indicator
        mode_color = (100, 255, 100) if self.use_cv else (255, 255, 100)
        mode_text = "HAND TRACKING" if self.use_cv else "MOUSE MODE"
        mode_surf = self.small_font.render(mode_text, True, mode_color)
        self.screen.blit(mode_surf, (self.screen_w - mode_surf.get_width() - 20, 100))
        
        # Hand lost warning
        if self.hand_lost_timer > 0.1:
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                warning = self.font.render("! HAND LOST !", True, (255, 50, 50))
                rect = warning.get_rect(center=(self.screen_w // 200, 100))
                self.screen.blit(warning, rect)