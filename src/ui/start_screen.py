import pygame
import cv2
import os
import random
from src.game.falling_objects import FallingItem, Rarity
from src.game.asset_manager import AssetManager 

def fade(screen, width, height, fade_in=True, speed=5):
    """Handles smooth transitions between screens."""
    fade_surface = pygame.Surface((width, height))
    fade_surface.fill((0, 0, 0))
    
    alpha = 255 if fade_in else 0
    clock = pygame.time.Clock()
    
    running = True
    while running:
        fade_surface.set_alpha(alpha)
        if not fade_in:
            screen.blit(fade_surface, (0, 0))
        else:
            screen.fill((0, 0, 0))
            screen.blit(fade_surface, (0, 0))
            
        pygame.display.flip()
        clock.tick(60)
        
        if fade_in:
            alpha -= speed
            if alpha <= 0: running = False
        else:
            alpha += speed
            if alpha >= 255: running = False

class UIFallingManager:
    """Manages the decorative falling items in the menu background."""
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
        self.items.append(FallingItem(x, item_type, Rarity.COMMON, speed, self.assets))

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

class StartScreen:
    def __init__(self, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_prototype = pygame.font.Font(None, 36)

        manager = AssetManager().load_all()
        self.assets_dict = manager.assets
        self.sounds = manager.sounds
        self.music_paths = manager.music_paths

        if not pygame.mixer.music.get_busy(): 
            try:
                pygame.mixer.music.load(self.music_paths['menu'])
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Error playing menu music: {e}")

        self.background = self.assets_dict.get('start_background')
        self.title_img = self.assets_dict.get('title2')
        self.start_button = self.assets_dict.get('start_button')
        
        if self.start_button:
            orig_w, orig_h = self.start_button.get_size()
            self.button_scale = 0.4 
            self.start_button = pygame.transform.smoothscale(
                self.start_button, 
                (int(orig_w * self.button_scale), int(orig_h * self.button_scale))
            )

        padding = 10
        vertical_offset = -100
        
        title_h = self.title_img.get_height() if self.title_img else 200
        btn_h = self.start_button.get_height() if self.start_button else 150
        
        total_group_height = title_h + padding + btn_h
        group_start_y = ((self.screen_height - total_group_height) // 2) + vertical_offset

        if self.title_img:
            self.title_rect = self.title_img.get_rect(center=(self.screen_width // 2, group_start_y + title_h // 2))
        
        if self.start_button:
            self.button_rect = self.start_button.get_rect(center=(self.screen_width // 2, self.title_rect.bottom + padding + btn_h // 2))
        else:
            self.button_rect = pygame.Rect(self.screen_width//2 - 100, group_start_y + title_h + padding, 200, 75)

        self.prototype_y = self.screen_height - 120
        self.button_hovering = False
        self.falling = UIFallingManager(screen_width, screen_height, self.assets_dict)
        self.font_hints = pygame.font.Font(None, 48)
        
        self.snapshot = None

    def handle_event(self, event):
        """Returns 'start' if game should start, 'quit' to exit, None otherwise."""
        if event.type == pygame.MOUSEMOTION:
            self.button_hovering = self.button_rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if 'click' in self.sounds and self.sounds['click']:
                    self.sounds['click'].play()
                return 'start'
            if event.key == pygame.K_ESCAPE:
                return 'quit'

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                if 'click' in self.sounds and self.sounds['click']:
                    self.sounds['click'].play()
                return 'start'
        
        return None

    def capture_snapshot(self, screen):
        """Capture current screen state before fade."""
        self.snapshot = screen.copy()
        return self.snapshot

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

    def render(self, screen):
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((235, 220, 207))
            
        self.falling.render(screen)
        
        # Render title invis for now
        #if self.title_img:
        #    screen.blit(self.title_img, self.title_rect)

        if self.start_button:
            if self.button_hovering:
                hover_scale = 1.05
                orig_w, orig_h = self.start_button.get_size()
                scaled_button = pygame.transform.smoothscale(self.start_button, (int(orig_w * hover_scale), int(orig_h * hover_scale)))
                screen.blit(scaled_button, scaled_button.get_rect(center=self.button_rect.center))
            else:
                screen.blit(self.start_button, self.button_rect)
        
        prototype_text = self._render_text_with_border("PROTOTYPE by: GAMEFRICKS", self.font_prototype, (255, 255, 255), (0, 0, 0))
        screen.blit(prototype_text, prototype_text.get_rect(center=(self.screen_width // 2, self.prototype_y)))
        
        space_hint = self._render_text_with_border("Press 'SPACE' to Play", self.font_hints, (255, 255, 255), (0, 0, 0))
        esc_hint = self._render_text_with_border("Press 'ESC' to Quit", self.font_hints, (255, 255, 255), (0, 0, 0))
        
        hint_y_start = self.button_rect.bottom + 60
        screen.blit(space_hint, space_hint.get_rect(center=(self.screen_width // 2, hint_y_start)))
        screen.blit(esc_hint, esc_hint.get_rect(center=(self.screen_width // 2, hint_y_start + 50)))

def show_start_screen(screen, screen_width=1920, screen_height=1080, gesture_controller=None):
    """Main loop for the Start Screen."""
    clock = pygame.time.Clock()
    start_screen = StartScreen(screen_width, screen_height)

    while True:
        dt = clock.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, None
            
            action = start_screen.handle_event(event)
            if action == 'start':
                # CAPTURE SCREEN BEFORE ANYTHING ELSE
                snapshot = start_screen.capture_snapshot(screen)
                pygame.mixer.music.fadeout(1000)
                # No fade - let wheel handle transition
                return True, snapshot
            elif action == 'quit':
                # Fade for quit
                fade(screen, screen_width, screen_height, fade_in=False)
                return False, None
        
        # UPDATE CAMERA FEED
        if gesture_controller:
            gesture_controller.update()
            debug_frame = gesture_controller.get_debug_frame()
            if debug_frame is not None:
                cv2.imshow("GAMEFRICKS PROTOTYPE01 - Camera Feed", debug_frame)
                cv2.waitKey(1)
        
        # Update and render UI
        start_screen.falling.update(dt)
        start_screen.render(screen)
        pygame.display.flip()