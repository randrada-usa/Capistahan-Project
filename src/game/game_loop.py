import pygame
import sys
import cv2
import random
from src.game.player import Player
from src.game.falling_objects import ObjectManager, Rarity
from src.game.game_state import GameState


# ==========================================
# TIMER CONFIGURATION
# ==========================================
TIMER_POSITION = "bottom_left"
TIMER_OFFSET_X = 50
TIMER_OFFSET_Y = 50
# ==========================================

CV_WINDOW_NAME = "GAMEFRICKS PROTOTYPE01 - Camera Feed"


class PerlaHUD:
    """
    Perla character that reacts to catches above wish progress bar.
    Category-specific sprites with expression states.
    """
    
    def __init__(self, asset_manager, theme_manager, x=170, y=290):
        self.assets = asset_manager
        self.theme = theme_manager.get_theme() if theme_manager else 'food'
        self.x = x
        self.y = y
        self.base_y = y
        
        # Animation states
        self.is_jumping = False
        self.jump_offset = 0
        self.jump_velocity = 0
        
        # Expression states
        self.current_expression = 'default'
        self.expression_timer = 0
        self.expression_duration = 0
        
        # Load category-specific sprites
        self._load_sprites()
        
    def _load_sprites(self):
        """Load perla sprites based on category."""
        # Map categories to their default sprite files
        default_sprites = {
            'food': 'perla_food',  # assets\sprites\new_sprites\perla_food.png
            'culture': 'perla_culture',    # assets\sprites\new_sprites\perla_culture.png  
            'people': 'perla_people'       # assets\sprites\new_sprites\perla_people.png
        }
        
        # Try to load new sprites first, fallback to old naming
        self.sprites = {
            'default': self._load_sprite(default_sprites.get(self.theme, 'perla_default')),
            'shock': self._load_sprite('1shock_perla'),      # Ultra Rare
            'smiley': self._load_sprite('1smiley_perla'),    # Rare
            'happy': self._load_sprite('1happy_perla'),      # Common/Very Common
            'angry': self._load_sprite('1angry_perla')       # Bad
        }
        
        # Fallback to default if specific not found
        for key in self.sprites:
            if self.sprites[key] is None:
                self.sprites[key] = self.sprites['default']
                
    def _load_sprite(self, name):
        """Helper to load sprite from new_sprites folder."""
        # Try new path first
        sprite = self.assets.get(name)
        if sprite is None:
            # Try loading manually if asset_manager doesn't have it
            try:
                import os
                path = os.path.join('assets', 'sprites', 'new_sprites', f'{name}.png')
                if os.path.exists(path):
                    sprite = pygame.image.load(path).convert_alpha()
                    sprite = pygame.transform.scale(sprite, (250, 250))  # Scale to appropriate size
            except:
                pass
        else:
            # Scale if loaded from asset manager
            if sprite:
                sprite = pygame.transform.scale(sprite, (250, 250))
        return sprite
        
    def react_to_catch(self, item):
        """
        Change expression and jump based on item caught.
        Handles rapid catches by immediately switching expression.
        """
        if item.type == 'bad':
            self.set_expression('angry', 1.5)
            # No jump for bad items
        elif item.rarity == Rarity.WISH:
            self.set_expression('shock', 3.0)
        elif item.rarity == Rarity.ULTRA_RARE:
            self.set_expression('shock', 2.0)
            self.jump(15)  # Big jump
        elif item.rarity == Rarity.RARE:
            self.set_expression('smiley', 1.5)
            self.jump(10)  # Medium jump
        else:  # Common or Very Common
            self.set_expression('happy', 1.0)
            # No jump for common items
            
    def set_expression(self, expression, duration):
        """Set expression immediately (interrupts current)."""
        self.current_expression = expression
        self.expression_duration = duration
        self.expression_timer = duration
        
    def jump(self, velocity):
        """Trigger jump animation."""
        if not self.is_jumping:  # Only jump if not already jumping
            self.is_jumping = True
            self.jump_velocity = -velocity  # Negative = up
            
    def update(self, dt):
        """Update animations."""
        # Expression timer
        if self.expression_timer > 0:
            self.expression_timer -= dt
            if self.expression_timer <= 0:
                self.current_expression = 'default'
                
        # Jump physics
        if self.is_jumping:
            self.jump_offset += self.jump_velocity
            self.jump_velocity += 40 * dt  # Gravity
            
            # Land
            if self.jump_offset >= 0:
                self.jump_offset = 0
                self.is_jumping = False
                self.jump_velocity = 0
                
    def render(self, screen):
        """Draw Perla above wish progress bar."""
        draw_y = self.y + self.jump_offset
        
        sprite = self.sprites.get(self.current_expression, self.sprites['default'])
        
        if sprite:
            # Center on x position
            rect = sprite.get_rect(center=(self.x, draw_y))
            screen.blit(sprite, rect)
            
            # Debug: Draw indicator of what expression is showing (remove in final)
            # font = pygame.font.Font(None, 24)
            # label = font.render(self.current_expression, True, (255,255,255))
            # screen.blit(label, (self.x - 30, draw_y - 50))


class CornerChibi:
    """Simplified - no expressions, just static display."""
    
    def __init__(self, asset_manager, x=150, y=20):
        self.assets = asset_manager
        self.x = x
        self.y = y
        
    def react_to_catch(self, item):
        pass  # No longer handles expressions
        
    def update(self, dt):
        pass  # No animations
        
    def render(self, screen):
        """Just draw static sprite if available."""
        sprite = self.assets.get('corner_chibi')
        if sprite:
            screen.blit(sprite, (self.x, self.y))


class GameLoop:
    """Main gameplay loop."""
    
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
        
        # Perla HUD - above wish progress bar (position adjusted for your layout)
        self.perla_hud = PerlaHUD(assets, theme_manager, x=170, y=170)
        
        # Static corner decoration (no longer shows expressions)
        self.corner_chibi = CornerChibi(assets, x=200, y=100)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.hand_lost_timer = 0
        
        # Fonts
        self.timer_font = pygame.font.Font(None, 72)
        self.timer_small_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        
        self.scale_func = scale_func if scale_func else lambda s: pygame.display.flip()        
        print(f"[GameLoop] Ready - Theme: {theme_manager.get_theme()}, CV: {self.use_cv}")
    
    def run(self):
        """Run gameplay until game over or quit."""
        print("[GameLoop] Starting game loop...")
        
        self.game_state.start_timer()
        
        while not self.game_state.game_over and self.running:
            dt = self.clock.tick(60) / 1000.0
            
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
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
            
            if not self.use_cv and event.type == pygame.MOUSEMOTION:
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
        self.perla_hud.update(dt)  # Update Perla animations
        self.corner_chibi.update(dt)
        
        # Collisions
        caught, _ = self.object_manager.check_collisions(
            self.player.get_hitbox()
        )
        
        for item in caught:
            self.game_state.handle_caught([item])
            # Send reaction to Perla HUD immediately (handles rapid fire)
            self.perla_hud.react_to_catch(item)
        
        self.game_state.check_game_over()

    def render(self):
        """Render everything."""
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
        
        # Scale to actual display
        self.scale_func(self.screen)
        
        # Camera display
        if self.use_cv:
            try:
                debug_frame = self.gesture_controller.get_debug_frame()
                if debug_frame is not None:
                    cv2.imshow(CV_WINDOW_NAME, debug_frame)
                    cv2.waitKey(1)
            except Exception as e:
                print(f"[GameLoop] CV display error: {e}")

    def _draw_hud(self):
        """Draw HUD."""
        # Score (top-right)
        score_text = self.font.render(f"Score: {self.game_state.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.screen_w - score_text.get_width() - 200, 80))
        
        # TIMER DISPLAY
        self._draw_timer()
        
        # Wish progress with Perla above it
        self.perla_hud.render(self.screen)  # Draw Perla first (behind text if overlap)
        
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
            wish_text = self.small_font.render("WISH READY!", True, (255, 215, 0))
            self.screen.blit(wish_text, (20, 340))
        
        # Hand lost warning - CENTERED AT TOP
        if self.hand_lost_timer > 0.1:
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                warning = self.font.render("! HAND LOST !", True, (255, 50, 50))
                rect = warning.get_rect(center=(self.screen_w // 2, 80))
                self.screen.blit(warning, rect)
    
    def _draw_timer(self):
        """Draw timer."""
        bar_width = 300
        bar_height = 20
        text_height = 55
        
        x, y = self._get_timer_position(bar_width, bar_height + text_height + 10)
        
        pygame.draw.rect(self.screen, (50, 50, 50), 
                        (x, y + text_height, bar_width, bar_height), border_radius=10)
        
        time_pct = self.game_state.get_time_percentage()
        fill_width = int(bar_width * time_pct)
        
        if time_pct > 0.5:
            color = (0, 255, 100)
        elif time_pct > 0.25:
            color = (255, 215, 0)
        else:
            color = (255, 50, 50)
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, 
                            (x, y + text_height, fill_width, bar_height), border_radius=10)
        
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (x, y + text_height, bar_width, bar_height), 2, border_radius=10)
        
        time_str = self.game_state.get_formatted_time()
        time_text = self.timer_font.render(time_str, True, (255, 255, 255))
        self.screen.blit(time_text, (x, y))
        
        label_text = self.timer_small_font.render("TIME REMAINING", True, (200, 200, 200))
        self.screen.blit(label_text, (x, y + text_height + bar_height + 5))
        
    def _get_timer_position(self, timer_width, timer_height):
        """Calculate timer position."""
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
            x = TIMER_OFFSET_X
            y = self.screen_h - timer_height - TIMER_OFFSET_Y
        
        return x, y