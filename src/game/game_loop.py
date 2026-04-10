import pygame
import sys
import cv2
import random
from src.game.player import Player
from src.game.falling_objects import ObjectManager, Rarity
from src.game.game_state import GameState


# ==========================================
# TIMER CONFIGURATION - Change position here
# ==========================================
TIMER_POSITION = "bottom_left"  # Options: "top_left", "top_right", "bottom_left", "bottom_right"
TIMER_OFFSET_X = 50  # Pixels from left/right edge
TIMER_OFFSET_Y = 50  # Pixels from top/bottom edge
# ==========================================

# Consistent window name with other screens
CV_WINDOW_NAME = "GAMEFRICKS PROTOTYPE01 - Camera Feed"


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
    
    def __init__(self, screen, assets, theme_manager, gesture_controller=None, 
                 use_cv=False, scale_func=None):
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
        
        # Timer font setup
        self.timer_font = pygame.font.Font(None, 72)
        self.timer_small_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)

        # Use consistent window name with other screens
        self._cv_window_created = False
        
        self.scale_func = scale_func if scale_func else lambda s: pygame.display.flip()        
        print(f"[GameLoop] Ready - Theme: {theme_manager.get_theme()}, CV: {self.use_cv}")
    
    def run(self):
        """Run gameplay until game over or quit."""
        print("[GameLoop] Starting game loop...")
        
        # Start the timer when gameplay begins
        self.game_state.start_timer()
        
        while not self.game_state.game_over and self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # CRITICAL: Always pump pygame events to prevent "Not Responding"
            pygame.event.pump()
            
            if not self.handle_events():
                return {'continue': False, 'game_state': None, 'snapshot': None}
            
            self.update(dt)
            self.render()
        
        print(f"[GameLoop] Game ended. Score: {self.game_state.score}")
        return {
            'continue': True,
            'game_state': self.game_state,
            'snapshot': self.screen.copy()
        }
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            
            # HANDLE RESIZE
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
            
            if not self.use_cv and event.type == pygame.MOUSEMOTION:
                # Use virtual mouse pos for player control too
                from src.ui.start_screen import get_mouse_pos_virtual
                virtual_pos = get_mouse_pos_virtual()
                if virtual_pos:
                    self.player.set_target_x(virtual_pos[0])
        
        return True

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
                self.use_cv = False
        
        self.player.update(dt)
        self.object_manager.update(dt, self.game_state.score)
        
        # Collisions - removed missed_good penalty
        caught, _ = self.object_manager.check_collisions(
            self.player.get_hitbox()
        )
        
        for item in caught:
            self.game_state.handle_caught([item])
            self.corner_chibi.react_to_catch(item)
            
            if item.rarity == Rarity.ULTRA_RARE:
                self.player.set_expression('super_excited', 1.0)
            elif item.rarity == Rarity.RARE:
                self.player.set_expression('excited', 0.5)
        
        # Check game over (now checks timer)
        self.game_state.check_game_over()
        self.corner_chibi.update(dt)

    def render(self):
        """Render everything to virtual screen, then scale to actual."""
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
        
        # CRITICAL: Scale to actual display using provided function
        self.scale_func(self.screen)
        
        # Camera display - use consistent window name
        if self.use_cv:
            self._update_camera_display()
            try:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC in CV window
                    pass
            except Exception as e:
                print(f"[GameLoop] cv2.waitKey error: {e}")
                self.use_cv = False

    def _update_camera_display(self):
        """Push the latest debug frame to the camera window."""
        if not self.gesture_controller:
            return
        
        try:
            debug_frame = self.gesture_controller.get_debug_frame()
            
            if debug_frame is not None:
                # Use the same window name as main.py and other screens
                cv2.imshow(CV_WINDOW_NAME, debug_frame)

        except Exception as e:
            print(f"[GameLoop] Camera display error (disabling): {e}")
            self.use_cv = False

    def _get_timer_position(self, timer_width, timer_height):
        """Calculate timer position based on TIMER_POSITION config."""
        if TIMER_POSITION == "bottom_left":
            x = TIMER_OFFSET_X
            y = self.screen_h - timer_height - TIMER_OFFSET_Y
        elif TIMER_POSITION == "bottom_right":
            x = self.screen_w - timer_width - TIMER_OFFSET_X
            y = self.screen_h - timer_height - TIMER_OFFSET_Y
        elif TIMER_POSITION == "top_left":
            x = TIMER_OFFSET_X
            y = TIMER_OFFSET_Y
        elif TIMER_POSITION == "top_right":
            x = self.screen_w - timer_width - TIMER_OFFSET_X
            y = TIMER_OFFSET_Y
        else:
            # Default bottom left
            x = TIMER_OFFSET_X
            y = self.screen_h - timer_height - TIMER_OFFSET_Y
        
        return x, y

    def _draw_hud(self):
        """Draw HUD with Timer instead of Health."""
        # Score (top-right) - MOVED UP slightly to make room for hand lost
        score_text = self.font.render(f"Score: {self.game_state.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.screen_w - score_text.get_width() - 200, 80))
        
        # REMOVED: Category/Theme indicator (Capiz Traditions 1.2x)
        # REMOVED: Input mode indicator (HAND TRACKING/MOUSE MODE)
        
        # TIMER DISPLAY - Bottom
        self._draw_timer()
        
        # Wish progress 
        if not self.game_state.is_wish_eligible():
            status = self.game_state.get_wish_status()
            bar_w = 300
            bar_h = 20
            bar_x = 20
            bar_y = 340
            
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (bar_x, bar_y, bar_w, bar_h), border_radius=10)
            fill_w = int(bar_w * (status['progress_percent'] / 100))
            bar_color = (255, 215, 0) if status['eligible'] else (150, 150, 150)
            pygame.draw.rect(self.screen, bar_color, 
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
            self.screen.blit(wish_text, (20, 340))
        
        # Hand lost warning - CENTERED AT TOP
        if self.hand_lost_timer > 0.1:
            if (pygame.time.get_ticks() // 200) % 2 == 0:  # Blink effect
                warning = self.font.render("! HAND LOST !", True, (255, 50, 50))
                rect = warning.get_rect(center=(self.screen_w // 2, 80))  # Center top
                self.screen.blit(warning, rect)
    
    def _draw_timer(self):
        """Draw the game timer with visual bar."""
        # INCREASED text_height from 40 to 55 to move number up
        bar_width = 300
        bar_height = 20
        text_height = 55  # Was 40, now 55 - moves number higher above bar
        
        # Get position based on config
        x, y = self._get_timer_position(bar_width, bar_height + text_height + 10)
        
        # Background bar (dark gray)
        pygame.draw.rect(self.screen, (50, 50, 50), 
                        (x, y + text_height, bar_width, bar_height), border_radius=10)
        
        # Time remaining fill (color changes based on urgency)
        time_pct = self.game_state.get_time_percentage()
        fill_width = int(bar_width * time_pct)
        
        if time_pct > 0.5:
            color = (0, 255, 100)  # Green
        elif time_pct > 0.25:
            color = (255, 215, 0)  # Yellow/Gold
        else:
            color = (255, 50, 50)   # Red (critical)
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, 
                            (x, y + text_height, fill_width, bar_height), border_radius=10)
        
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (x, y + text_height, bar_width, bar_height), 2, border_radius=10)
        
        # Time text (above bar) - Now with more spacing due to text_height=55
        time_str = self.game_state.get_formatted_time()
        time_text = self.timer_font.render(time_str, True, (255, 255, 255))
        self.screen.blit(time_text, (x, y))
        
        # "TIME" label
        label_text = self.timer_small_font.render("TIME REMAINING", True, (200, 200, 200))
        self.screen.blit(label_text, (x, y + text_height + bar_height + 5))