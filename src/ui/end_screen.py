"""
end_screen.py - Fixed with SFX playing at video START and bg music stopped
"""

import pygame
import cv2
import os
import random
import numpy as np
from src.game.falling_objects import FallingItem, Rarity
from src.game.asset_manager import AssetManager
from src.game.wish_system import make_wish


def play_wish_video(screen, video_path, scale_func=None, sfx_sound=None):
    """
    Play a wish video using OpenCV.
    Press any key or click to skip.
    
    Args:
        screen: pygame screen surface
        video_path: path to video file
        scale_func: function to scale and flip screen
        sfx_sound: pygame Sound object to play when video starts
    """
    if not video_path or not os.path.exists(video_path):
        print(f"[play_wish_video] Video not found: {video_path}")
        return False
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[play_wish_video] Failed to open: {video_path}")
        return False
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    clock = pygame.time.Clock()
    target_w, target_h = screen.get_size()
    
    print(f"[play_wish_video] Playing: {video_path}")
    
    # ✅ STOP BACKGROUND MUSIC AND PLAY SFX AT VIDEO START
    first_frame = True
    sfx_played = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # ✅ On first frame: stop bg music and play SFX
        if first_frame:
            # Stop background music
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                print("[play_wish_video] Stopped background music")
            
            # Play SFX
            if sfx_sound and not sfx_played:
                sfx_sound.play()
                sfx_played = True
                print(f"[play_wish_video] Playing SFX at video start")
            
            first_frame = False
        
        # Handle skip events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                return False
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                cap.release()
                return True
        
        # Convert BGR to RGB, resize, and create surface
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, (target_w, target_h))
        
        # Transpose for pygame (OpenCV uses HxWxC, pygame needs WxHxC)
        frame_rgb = np.transpose(frame_rgb, (1, 0, 2))
        surface = pygame.surfarray.make_surface(frame_rgb)
        
        screen.blit(surface, (0, 0))
        
        if scale_func:
            scale_func(screen)
        else:
            pygame.display.flip()
        
        clock.tick(fps)
    
    cap.release()
    return True

def get_mouse_pos_virtual():
    """Convert actual window mouse pos to virtual 1920x1080 coordinates."""
    actual_surface = pygame.display.get_surface()
    if actual_surface is None:
        return pygame.mouse.get_pos()
    
    actual_w, actual_h = actual_surface.get_size()
    virtual_w, virtual_h = 1920, 1080
    
    scale = min(actual_w / virtual_w, actual_h / virtual_h)
    new_w = int(virtual_w * scale)
    new_h = int(virtual_h * scale)
    
    offset_x = (actual_w - new_w) // 2
    offset_y = (actual_h - new_h) // 2
    
    mx, my = pygame.mouse.get_pos()
    
    if mx < offset_x or mx >= offset_x + new_w or my < offset_y or my >= offset_y + new_h:
        return None
    
    virtual_x = int((mx - offset_x) / scale)
    virtual_y = int((my - offset_y) / scale)
    
    return (virtual_x, virtual_y)

class UIFallingManager:
    """Manages decorative falling items for the background."""
    
    RARITY_WEIGHTS = {
        Rarity.VERY_COMMON: 0.35,
        Rarity.COMMON: 0.40,
        Rarity.RARE: 0.20,
        Rarity.ULTRA_RARE: 0.05
    }
    
    CATEGORIES = ['food', 'people']
    
    def __init__(self, screen_width, screen_height, assets=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = assets
        self.items = []
        self.spawn_timer = 0

    def spawn_item(self):
        x = random.randint(60, self.screen_width - 60)
        item_type = 'good'
        
        rarities = list(self.RARITY_WEIGHTS.keys())
        weights = list(self.RARITY_WEIGHTS.values())
        rarity = random.choices(rarities, weights=weights, k=1)[0]
        
        speed = random.uniform(2, 4)
        item = FallingItem(x, item_type, rarity, speed, self.assets, None)
        
        category = random.choice(self.CATEGORIES)
        
        rarity_prefixes = {
            Rarity.VERY_COMMON: 'ultracommon',
            Rarity.COMMON: 'common',
            Rarity.RARE: 'rare',
            Rarity.ULTRA_RARE: 'ultrarare'
        }
        prefix = rarity_prefixes[rarity]
        
        item.item_key = f'{category}_{prefix}'
        item.category = category
        
        self.items.append(item)

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
    def __init__(self, screen_width=1920, screen_height=1080, show_wish_button=True):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.show_wish_button = show_wish_button

        self.font_score = pygame.font.Font(None, 74)
        self.font_high = pygame.font.Font(None, 48)
        self.font_prototype = pygame.font.Font(None, 36)
        self.font_hints = pygame.font.Font(None, 36)
        self.font_wish = pygame.font.Font(None, 60)

        manager = AssetManager().load_all()
        self.assets_dict = manager.assets
        self.sounds = manager.sounds
        self.music_paths = manager.music_paths

        # ✅ LOAD BUTTONSTART.mp3 SFX for buttons
        self.button_sfx = None
        button_sfx_path = os.path.join("assets", "audio", "BUTTONSTART.mp3")
        if os.path.exists(button_sfx_path):
            try:
                self.button_sfx = pygame.mixer.Sound(button_sfx_path)
                print(f"[EndScreen] Loaded BUTTONSTART.mp3")
            except Exception as e:
                print(f"[EndScreen] Failed to load BUTTONSTART.mp3: {e}")

        # ✅ LOAD WISH SFX
        self.wish_good_sfx = None
        self.wish_bad_sfx = None
        
        good_sfx_path = os.path.join("assets", "audio", "GOOD.mp3")
        bad_sfx_path = os.path.join("assets", "audio", "BAD.mp3")
        
        if os.path.exists(good_sfx_path):
            try:
                self.wish_good_sfx = pygame.mixer.Sound(good_sfx_path)
                print(f"[EndScreen] Loaded GOOD.mp3 (wish granted SFX)")
            except Exception as e:
                print(f"[EndScreen] Failed to load GOOD.mp3: {e}")
            
        if os.path.exists(bad_sfx_path):
            try:
                self.wish_bad_sfx = pygame.mixer.Sound(bad_sfx_path)
                print(f"[EndScreen] Loaded BAD.mp3 (no wish SFX)")
            except Exception as e:
                print(f"[EndScreen] Failed to load BAD.mp3: {e}")

        self.button_scale = 0.5 
        
        self.retry_btn_img = self.assets_dict.get('retry_button')
        if self.retry_btn_img:
            r_w, r_h = self.retry_btn_img.get_size()
            self.retry_btn_img = pygame.transform.smoothscale(self.retry_btn_img, (int(r_w * self.button_scale), int(r_h * self.button_scale)))

        self.menu_btn_img = self.assets_dict.get('menu_button')
        if self.menu_btn_img:
            m_w, m_h = self.menu_btn_img.get_size()
            self.menu_btn_img = pygame.transform.smoothscale(self.menu_btn_img, (int(m_w * self.button_scale), int(m_h * self.button_scale)))

        self.wish_btn_img = self.assets_dict.get('start_button')
        if self.wish_btn_img:
            w_w, w_h = self.wish_btn_img.get_size()
            self.wish_scale = 0.6
            self.wish_btn_img = pygame.transform.smoothscale(self.wish_btn_img, (int(w_w * self.wish_scale), int(w_h * self.wish_scale)))

        btn_w = self.retry_btn_img.get_width() if self.retry_btn_img else 200
        btn_h = self.retry_btn_img.get_height() if self.retry_btn_img else 100
        spacing = 40
        
        total_width = (btn_w * 2) + spacing
        start_x = (self.screen_width - total_width) // 2
        btn_y = (self.screen_height // 2) + 100

        self.retry_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        self.menu_rect = pygame.Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)
        
        if self.wish_btn_img:
            wish_w = self.wish_btn_img.get_width()
            wish_h = self.wish_btn_img.get_height()
        else:
            wish_w, wish_h = btn_w, btn_h
        
        self.wish_rect = pygame.Rect(0, 0, wish_w, wish_h)
        self.wish_rect.centerx = self.screen_width // 2
        self.wish_rect.centery = btn_y - 100

        self.retry_hovering = False
        self.menu_hovering = False
        self.wish_hovering = False
        
        self.falling = UIFallingManager(screen_width, screen_height, self.assets_dict)
        
        self.final_score = 0
        self.high_score = 0
        self.is_new_record = False
        self.overlay_alpha = 180 
        
        self.wish_result = None
        self.showing_wish_modal = False
        self.game_state = None
        self.wish_used = False

        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.load(self.music_paths['menu'])
                pygame.mixer.music.play(-1)
            except:
                pass

    def set_scores(self, final_score, high_score, is_new_record=False):
        self.final_score = final_score
        self.high_score = high_score
        self.is_new_record = is_new_record and (final_score > 0) and (final_score >= high_score)

    def set_game_state(self, game_state):
        self.game_state = game_state

    def _play_button_sound(self):
        """✅ Play BUTTONSTART.mp3 sound effect"""
        if self.button_sfx:
            self.button_sfx.play()
        elif 'click' in self.sounds:
            self.sounds['click'].play()

    def handle_event(self, event):
        virtual_pos = get_mouse_pos_virtual()
        
        if self.showing_wish_modal:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.showing_wish_modal = False
                self.wish_result = None
            return None

        if event.type == pygame.MOUSEMOTION:
            if virtual_pos:
                self.retry_hovering = self.retry_rect.collidepoint(virtual_pos)
                self.menu_hovering = self.menu_rect.collidepoint(virtual_pos)
                self.wish_hovering = self.wish_rect.collidepoint(virtual_pos)
            else:
                self.retry_hovering = False
                self.menu_hovering = False
                self.wish_hovering = False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self._play_button_sound()
                return "retry"
            if event.key == pygame.K_ESCAPE:
                return "quit"

        if event.type == pygame.MOUSEBUTTONDOWN and virtual_pos:
            if self.wish_rect.collidepoint(virtual_pos) and self.game_state and hasattr(self.game_state, 'is_wish_eligible') and self.game_state.is_wish_eligible() and not self.wish_used:
                self._play_button_sound()
                self._make_wish()
                return None
            if self.retry_rect.collidepoint(virtual_pos):
                self._play_button_sound()
                return "retry"
            if self.menu_rect.collidepoint(virtual_pos):
                self._play_button_sound()
                return "menu"

        return None

    def _make_wish(self):
        if self.game_state and not self.wish_used:
            self.wish_result = self.game_state.resolve_wish()
            self.showing_wish_modal = True
            self.wish_used = True

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

    def _draw_wish_modal(self, screen):
        if not self.wish_result:
            return
            
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        box_w, box_h = 800, 400
        box_x = (self.screen_width - box_w) // 2
        box_y = (self.screen_height - box_h) // 2
        
        if self.wish_result.get('won'):
            pygame.draw.rect(screen, (255, 215, 0), (box_x - 10, box_y - 10, box_w + 20, box_h + 20), border_radius=30)
            pygame.draw.rect(screen, (60, 40, 0), (box_x, box_y, box_w, box_h), border_radius=20)
            
            title = self.font_wish.render("★ GOLDEN TICKET ★", True, (255, 215, 0))
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, box_y + 60)))
            
            code_text = self.font_high.render(f"Code: {self.wish_result.get('code', 'XXXXXX')}", True, (0, 255, 0))
            screen.blit(code_text, code_text.get_rect(center=(self.screen_width // 2, box_y + 200)))
            
        else:
            pygame.draw.rect(screen, (100, 100, 100), (box_x - 10, box_y - 10, box_w + 20, box_h + 20), border_radius=30)
            pygame.draw.rect(screen, (40, 40, 60), (box_x, box_y, box_w, box_h), border_radius=20)
            
            title = self.font_wish.render("BETTER LUCK NEXT TIME", True, (200, 200, 200))
            screen.blit(title, title.get_rect(center=(self.screen_width // 2, box_y + 80)))
            
            msg = self.font_high.render(self.wish_result.get('message', 'Perla saw you effort! Try again later!'), True, (255, 255, 255))
            screen.blit(msg, msg.get_rect(center=(self.screen_width // 2, box_y + 160)))
        
        continue_text = self.font_hints.render("Click or press any key to continue...", True, (150, 150, 150))
        screen.blit(continue_text, continue_text.get_rect(center=(self.screen_width // 2, box_y + box_h - 50)))

    def _draw_wish_button(self, screen, eligible):
        if not self.show_wish_button or self.showing_wish_modal:
            return
        
        status = None
        if self.game_state and hasattr(self.game_state, 'get_wish_status'):
            status = self.game_state.get_wish_status()
        
        if eligible:
            btn_img = self.wish_btn_img
            if btn_img:
                if self.wish_hovering:
                    scaled = pygame.transform.smoothscale(btn_img, (int(btn_img.get_width()*1.05), int(btn_img.get_height()*1.05)))
                    screen.blit(scaled, scaled.get_rect(center=self.wish_rect.center))
                else:
                    screen.blit(btn_img, self.wish_rect)
            
            wish_text = self._render_text_with_border("MAKE A WISH!", self.font_high, (255, 215, 0), (0, 0, 0))
            screen.blit(wish_text, wish_text.get_rect(center=self.wish_rect.center))
        
        if status:
            bar_w = 300
            bar_h = 20
            bar_x = (self.screen_width - bar_w) // 2
            bar_y = self.wish_rect.bottom + 20
            
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
            progress_w = int(bar_w * (status['progress_percent'] / 100))
            bar_color = (255, 215, 0) if eligible else (150, 150, 150)
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, progress_w, bar_h), border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=10)
            
            progress_text = self.font_hints.render(f"{status['current']}/{status['threshold']} points", True, (255, 255, 255))
            screen.blit(progress_text, progress_text.get_rect(center=(self.screen_width // 2, bar_y + 40)))

    def render(self, screen, background_snapshot=None):
        if background_snapshot:
            screen.blit(background_snapshot, (0, 0))
        else:
            screen.fill((30, 30, 40))

        self.falling.render(screen)

        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.overlay_alpha)) 
        screen.blit(overlay, (0, 0))

        center_x = self.screen_width // 2
        score_y = self.retry_rect.top - 200
        
        score_text = self.font_score.render(f"Score: {self.final_score}", True, (255, 255, 255))
        screen.blit(score_text, score_text.get_rect(center=(center_x, score_y)))
        
        high_text = self.font_high.render(f"Best: {self.high_score}", True, (255, 215, 0))
        screen.blit(high_text, high_text.get_rect(center=(center_x, score_y + 60)))
        
        if self.is_new_record:
            record_text = self._render_text_with_border("NEW RECORD!", self.font_high, (255, 215, 0), (0, 0, 0))
            screen.blit(record_text, record_text.get_rect(center=(center_x, score_y + 110)))

        eligible = False
        if self.game_state and hasattr(self.game_state, 'is_wish_eligible'):
            eligible = self.game_state.is_wish_eligible()
        
        self._draw_wish_button(screen, eligible)

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
        
        retry_hint = self._render_text_with_border("'R' or SPACE: Retry", self.font_hints, (200, 200, 200), (0, 0, 0))
        menu_hint = self._render_text_with_border("'ESC': Menu", self.font_hints, (200, 200, 200), (0, 0, 0))
        
        hint_y = self.retry_rect.bottom + 50
        screen.blit(retry_hint, retry_hint.get_rect(center=(center_x - 100, hint_y)))
        screen.blit(menu_hint, menu_hint.get_rect(center=(center_x + 100, hint_y)))
        
        prototype_text = self._render_text_with_border("PROTOTYPE by: GAMEFRICKS", self.font_prototype, (255, 255, 255), (0, 0, 0))
        screen.blit(prototype_text, prototype_text.get_rect(center=(center_x, self.screen_height - 60)))
        
        if self.showing_wish_modal:
            self._draw_wish_modal(screen)


def show_end_screen(screen, game_state, 
                    background_snapshot=None, screen_width=1920, screen_height=1080,
                    gesture_controller=None, scale_func=None):
    """
    Shows the end screen.
    
    Returns:
        "retry" - Player wants to retry (go to wheel)
        "menu" - Player wants to go to menu/start screen
        None - Error or quit
    """
    # Create EndScreen early to access SFX sounds
    end_screen = EndScreen(screen_width, screen_height, show_wish_button=False)
    
    # Auto-resolve wish when game ends
    wish_result = make_wish(game_state.score, game_state.theme if hasattr(game_state, 'theme') else 'food')
    
    # ✅ Play all videos sequentially WITH SFX playing at video start (bg music stopped)
    if wish_result.get('video_paths'):
        for i, video_path in enumerate(wish_result['video_paths']):
            # Determine which SFX to play based on win/loss
            is_win = False
            if wish_result.get('wishes') and i < len(wish_result['wishes']):
                is_win = wish_result['wishes'][i].get('won', False)
            else:
                is_win = wish_result.get('won', False)
            
            # Select appropriate SFX
            sfx_to_play = None
            if is_win:
                sfx_to_play = end_screen.wish_good_sfx  # GOOD.mp3
                print(f"[show_end_screen] Will play GOOD.mp3 with win video (bg music will stop)")
            else:
                sfx_to_play = end_screen.wish_bad_sfx   # BAD.mp3
                print(f"[show_end_screen] Will play BAD.mp3 with loss video (bg music will stop)")
            
            # ✅ Play video with SFX starting at the same time (bg music stops automatically)
            play_wish_video(screen, video_path, scale_func, sfx_to_play)
    
    # Check result and return appropriate action
    if wish_result.get('won'):
        return "menu"  # Goes back to start screen if won
    
    # If all losses, show end screen without wish button
    final_score = game_state.score
    high_score = game_state.high_score if hasattr(game_state, 'high_score') else 0
    is_new_record = hasattr(game_state, 'is_new_high_score') and game_state.is_new_high_score()
    
    end_screen.set_scores(final_score, high_score, is_new_record)
    end_screen.set_game_state(game_state)
    
    # Store wish result for display in modal (show first loss message)
    if wish_result.get('wishes'):
        end_screen.wish_result = wish_result['wishes'][0]
    else:
        end_screen.wish_result = wish_result
    end_screen.showing_wish_modal = True
    
    clock = pygame.time.Clock()
    do_flip = scale_func if scale_func else lambda s: pygame.display.flip()
    
    running = True
    while running:
        dt = clock.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            # HANDLE RESIZE
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            action = end_screen.handle_event(event)
            
            if action == "retry":
                pygame.mixer.music.fadeout(1000)
                return "retry"
            elif action == "menu":
                pygame.mixer.music.fadeout(1000)
                return "menu"
            elif action == "quit":
                pygame.quit()
                exit()
        
        if gesture_controller:
            gesture_controller.update()
            debug_frame = gesture_controller.get_debug_frame()
            if debug_frame is not None:
                cv2.imshow("GAMEFRICKS PROTOTYPE01 - Camera Feed", debug_frame)
                cv2.waitKey(1)
        
        end_screen.falling.update(dt)
        end_screen.render(screen, background_snapshot)
        do_flip(screen)
    
    return "menu"