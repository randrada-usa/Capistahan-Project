import pygame
import cv2  # Added for camera window updates
import os
import random
from src.game.falling_objects import FallingItem
from src.game.asset_manager import AssetManager

class UIFallingManager:
    """Manages decorative falling items for the background."""
    def __init__(self, screen_width, screen_height, assets=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = assets
        self.items = []
        self.spawn_timer = 0

    def spawn_item(self):
        x = random.randint(60, self.screen_width - 60)
        item_type = 'good' if random.random() < 0.7 else 'bad'
        speed = random.uniform(2, 4) 
        self.items.append(FallingItem(x, item_type, speed, self.assets))

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer > 0.8:
            self.spawn_item()
            self.spawn_timer = 0

        for item in self.items:
            item.update(dt, 1.0)

        self.items = [
            item for item in self.items
            if not item.is_off_screen(self.screen_height)
        ]

    def render(self, screen):
        for item in self.items:
            item.render(screen)

def fade(screen, width, height, fade_in=True, speed=5):
    """Smoothly transitions screen alpha."""
    fade_surface = pygame.Surface((width, height))
    fade_surface.fill((0, 0, 0))
    
    alpha = 255 if fade_in else 0
    clock = pygame.time.Clock()
    
    running = True
    while running:
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        
        if fade_in:
            alpha -= speed
            if alpha <= 0: running = False
        else:
            alpha += speed
            if alpha >= 255: running = False

class EndScreen:
    def __init__(self, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Fonts
        self.font_score = pygame.font.Font(None, 74)
        self.font_high = pygame.font.Font(None, 48)
        self.font_prototype = pygame.font.Font(None, 36)
        self.font_hints = pygame.font.Font(None, 36)  # For keyboard hints

        # Asset & Audio Initialization
        manager = AssetManager().load_all()
        self.assets_dict = manager.assets
        self.sounds = manager.sounds
        self.music_paths = manager.music_paths

        # Button Setup
        self.button_scale = 0.5 
        
        # Load and scale Retry Button
        self.retry_btn_img = self.assets_dict.get('retry_button')
        if self.retry_btn_img:
            r_w, r_h = self.retry_btn_img.get_size()
            self.retry_btn_img = pygame.transform.smoothscale(self.retry_btn_img, (int(r_w * self.button_scale), int(r_h * self.button_scale)))

        # Load and scale Menu Button
        self.menu_btn_img = self.assets_dict.get('menu_button')
        if self.menu_btn_img:
            m_w, m_h = self.menu_btn_img.get_size()
            self.menu_btn_img = pygame.transform.smoothscale(self.menu_btn_img, (int(m_w * self.button_scale), int(m_h * self.button_scale)))

        # Positioning Buttons side-by-side
        btn_w = self.retry_btn_img.get_width() if self.retry_btn_img else 200
        btn_h = self.retry_btn_img.get_height() if self.retry_btn_img else 100
        spacing = 40
        
        total_width = (btn_w * 2) + spacing
        start_x = (self.screen_width - total_width) // 2
        btn_y = (self.screen_height // 2) + 100

        self.retry_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        self.menu_rect = pygame.Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)

        self.retry_hovering = False
        self.menu_hovering = False
        
        self.falling = UIFallingManager(screen_width, screen_height, self.assets_dict)
        
        self.final_score = 0
        self.high_score = 0
        self.is_new_record = False
        self.overlay_alpha = 180 

        # Ensure Menu Music is playing
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(self.music_paths['menu'])
            pygame.mixer.music.play(-1)

    def set_scores(self, final_score, high_score, is_new_record=False):
        self.final_score = final_score
        self.high_score = high_score
        # --- FIX: Validate that new record is actually higher than previous best ---
        # Only set is_new_record to True if final_score > high_score (the previous high)
        # Note: high_score passed here should be the PREVIOUS high score before updating
        self.is_new_record = is_new_record and (final_score > 0) and (final_score >= high_score)

    def handle_event(self, event):
        """Handle input events. Returns 'retry', 'menu', 'quit', or None."""
        if event.type == pygame.MOUSEMOTION:
            self.retry_hovering = self.retry_rect.collidepoint(event.pos)
            self.menu_hovering = self.menu_rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                if 'click' in self.sounds: self.sounds['click'].play()
                return "retry"
            # --- ADDED: ESC to quit from end screen ---
            if event.key == pygame.K_ESCAPE:
                return "quit"

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.retry_rect.collidepoint(event.pos):
                if 'click' in self.sounds: self.sounds['click'].play()
                return "retry"
            if self.menu_rect.collidepoint(event.pos):
                if 'click' in self.sounds: self.sounds['click'].play()
                return "menu"

        return None

    def _render_text_with_border(self, text, font, text_color, border_color, border_width=2):
        text_surface = font.render(text, True, text_color)
        border_surface = font.render(text, True, border_color)
        w, h = text_surface.get_size()
        bordered_surface = pygame.Surface((w + border_width * 2, h + border_width * 2), pygame.SRCALPHA)
        directions = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        for dx, dy in directions:
            bordered_surface.blit(border_surface, (border_width + dx * border_width, border_width + dy * border_width))
        bordered_surface.blit(text_surface, (border_width, border_width))
        return bordered_surface

    def render(self, screen, background_snapshot=None):
        # 1. Background (Frozen game)
        if background_snapshot:
            screen.blit(background_snapshot, (0, 0))
        else:
            screen.fill((30, 30, 40))

        # 2. Decorative Falling Items
        self.falling.render(screen)

        # 3. Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.overlay_alpha)) 
        screen.blit(overlay, (0, 0))

        center_x = self.screen_width // 2
        score_y = self.retry_rect.top - 200
        
        # 4. Score Text
        score_text = self.font_score.render(f"Score: {self.final_score}", True, (255, 255, 255))
        screen.blit(score_text, score_text.get_rect(center=(center_x, score_y)))
        
        high_text = self.font_high.render(f"Best: {self.high_score}", True, (255, 215, 0))
        screen.blit(high_text, high_text.get_rect(center=(center_x, score_y + 60)))
        
        # --- FIXED: Only show NEW RECORD if is_new_record is True (validated in set_scores) ---
        if self.is_new_record:
            record_text = self._render_text_with_border("NEW RECORD!", self.font_high, (255, 215, 0), (0, 0, 0))
            screen.blit(record_text, record_text.get_rect(center=(center_x, score_y + 110)))

        # 5. Render Buttons with Hover Effects
        for btn_img, btn_rect, is_hover in [
            (self.retry_btn_img, self.retry_rect, self.retry_hovering),
            (self.menu_btn_img, self.menu_rect, self.menu_hovering)
        ]:
            if btn_img:
                if is_hover:
                    scaled = pygame.transform.smoothscale(btn_img, (int(btn_img.get_width()*1.05), int(btn_img.get_height()*1.05)))
                    screen.blit(scaled, scaled.get_rect(center=btn_rect.center))
                else:
                    screen.blit(btn_img, btn_rect)
        
        # 6. Keyboard Hints
        retry_hint = self._render_text_with_border("'R' or SPACE: Retry", self.font_hints, (200, 200, 200), (0, 0, 0))
        menu_hint = self._render_text_with_border("'ESC': Menu", self.font_hints, (200, 200, 200), (0, 0, 0))
        
        hint_y = self.retry_rect.bottom + 50
        screen.blit(retry_hint, retry_hint.get_rect(center=(center_x - 100, hint_y)))
        screen.blit(menu_hint, menu_hint.get_rect(center=(center_x + 100, hint_y)))
        
        # 7. Credits
        prototype_text = self._render_text_with_border("PROTOTYPE by: GAMEFRICKS", self.font_prototype, (255, 255, 255), (0, 0, 0))
        screen.blit(prototype_text, prototype_text.get_rect(center=(center_x, self.screen_height - 60)))

def show_end_screen(screen, final_score, high_score, is_new_record=False, 
                    background_snapshot=None, screen_width=1920, screen_height=1080,
                    gesture_controller=None):
    """Main loop for the Game Over screen with persistent camera. Returns True to Restart, False to return to Menu."""
    end_screen = EndScreen(screen_width, screen_height)
    end_screen.set_scores(final_score, high_score, is_new_record)
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            
            action = end_screen.handle_event(event)
            if action == "retry":
                pygame.mixer.music.fadeout(1000) 
                fade(screen, screen_width, screen_height, fade_in=False)
                return True
            elif action == "menu":
                fade(screen, screen_width, screen_height, fade_in=False)
                return False
            elif action == "quit":
                # --- ADDED: Handle quit action from ESC key ---
                fade(screen, screen_width, screen_height, fade_in=False)
                return False  # Return to menu (or could exit game entirely)
        
        # UPDATE CAMERA FEED - Keep the CV window live during game over screen!
        if gesture_controller:
            gesture_controller.update()  # Process frame to keep feed active
            debug_frame = gesture_controller.get_debug_frame()
            if debug_frame is not None:
                cv2.imshow("GAMEFRICKS PROTOTYPE01 - Camera Feed", debug_frame)
                cv2.waitKey(1)  # Required for OpenCV window to process events
        
        end_screen.falling.update(dt)
        end_screen.render(screen, background_snapshot)
        pygame.display.flip()