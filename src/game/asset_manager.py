"""
Asset Manager - Loads themed assets for Capiztahan.
"""

import pygame
import os
import sys
from src.game.theme_manager import ThemeManager


def resource_path(relative_path):
    """Get absolute path to assets folder."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets")


def log(msg):
    """Print only in development."""
    if not getattr(sys, 'frozen', False):
        print(msg)


class AssetManager:
    def __init__(self, theme='food'):
        self.assets = {}
        self.sounds = {}
        self.music_paths = {}
        self.theme_manager = ThemeManager(theme)
        self.base_path = resource_path("")
        
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                log(f"[AssetManager] Mixer init failed: {e}")
        
        self.fallbacks_used = []
    
    def load_all(self):
        """Load all assets for the current theme."""
        theme = self.theme_manager.get_theme()
        log(f"[AssetManager] Loading assets for theme: {theme}")
        log(f"[AssetManager] Base path: {self.base_path}")

        # --- WHEEL SCREEN ASSETS (Shared) ---
        self._load_shared('wheel_base', os.path.join("ui", "wheel.png"))
        self._load_shared('perla_food', os.path.join("ui", "perla_food.png"), target_size=(285, 285))
        self._load_shared('perla_culture', os.path.join("ui", "perla_culture.png"), target_size=(285, 285))
        self._load_shared('perla_people', os.path.join("ui", "perla_people.png"), target_size=(285, 285))
        
        # --- UI ASSETS ---
        self._load_shared('start_button', os.path.join("ui", "start_button2.png"))
        self._load_shared('retry_button', os.path.join("ui", "retry_button2.png"))
        self._load_shared('menu_button', os.path.join("ui", "back_button2.png"))
        self._load_shared('title2', os.path.join("ui", "WAVE&WISH.png"))


        self._load_shared('wish_glow', os.path.join("effects", "wish_glow.png"), (130, 130))
        self._load_shared('wish_item', os.path.join("sprites", "new_sprites", "wish.png"), (100, 100))
        self._load_shared('wish_book', os.path.join("sprites", "new_sprites", "wish.png"), (100, 100))

        self._load_shared('culture_angry', os.path.join("culture", "sprites", "culture_angry.png"), (250, 250))
        self._load_shared('culture_happy', os.path.join("culture", "sprites", "culture_happy.png"), (250, 250))
        self._load_shared('culture_shock', os.path.join("culture", "sprites", "culture_shock.png"), (250, 250))

        self._load_shared('food_angry', os.path.join("food", "sprites", "food_angry.png"), (250, 250))
        self._load_shared('food_happy', os.path.join("food", "sprites", "food_happy.png"), (250, 250))
        self._load_shared('food_shock', os.path.join("food", "sprites", "food_shock.png"), (250, 250))

        self._load_shared('people_angry', os.path.join("people", "sprites", "people_angry.png"), (250, 250))
        self._load_shared('people_happy', os.path.join("people", "sprites", "people_happy.png"), (250, 250))
        self._load_shared('people_shock', os.path.join("people", "sprites", "people_shock.png"), (250, 250))
        
        # --- GLOBAL EFFECTS (Glows) ---
        self._load_shared('common_glow', os.path.join("effects", "common_glow.png"), (150, 150))
        self._load_shared('rare_glow', os.path.join("effects", "rare_glow.png"), (150, 150))
        self._load_shared('ultra_rare_glow', os.path.join("effects", "ultra_rare_glow.png"), (150, 150))

        # --- THEME-SPECIFIC PLAYER SPRITES
        # Left direction frames
        self._load_themed('new_sprite_left', 
                         os.path.join("sprites", "new_sprites", "new_sprite_left.png"), 
                         target_size=(260, 380))
        self._load_themed('new_sprite_left_extend', 
                         os.path.join("sprites", "new_sprites", "new_sprite_left_extend.png"), 
                         target_size=(260, 380))
        
        # Right direction frames  
        self._load_themed('new_sprite_right', 
                         os.path.join("sprites", "new_sprites", "new_sprite_right.png"), 
                         target_size=(260, 380))
        self._load_themed('new_sprite_right_extend', 
                         os.path.join("sprites", "new_sprites", "new_sprite_right_extend.png"), 
                         target_size=(260, 380))
        
        # Idle frame
        self._load_themed('new_sprite_default', 
                         os.path.join("sprites", "new_sprites", "new_sprite(default).png"), 
                         target_size=(260, 380))
        
        # --- SHARED START/END SCREEN BACKGROUND ---
        self._load_shared('start_background', os.path.join("backgrounds", "bg1.png"), target_size=(1920, 1080))
        
        # --- THEME-SPECIFIC GAMEPLAY BACKGROUNDS ---
        if theme == 'food':
            self._load_themed('background', os.path.join("background", "food_bg.png"), target_size=(1920, 1080))
        elif theme == 'culture':
            self._load_themed('background', os.path.join("background", "bg_culture.png"), target_size=(1920, 1080))
        elif theme == 'people':
            self._load_themed('background', os.path.join("background", "people_bg.png"), target_size=(1920, 1080))
        
        # --- THEME-SPECIFIC ITEMS (for gameplay) ---
        if theme == 'people':
            item_suffix = 'book'
        else:
            item_suffix = 'item'
        
        self._load_themed(f'ultracommon_{item_suffix}', 
                         os.path.join("sprites", f"ultracommon_{item_suffix}.png"), 
                         target_size=(110, 110))
        self._load_themed(f'common_{item_suffix}', 
                         os.path.join("sprites", f"common_{item_suffix}.png"), 
                         target_size=(110, 110))
        self._load_themed(f'rare_{item_suffix}', 
                         os.path.join("sprites", f"rare_{item_suffix}.png"), 
                         target_size=(110, 110))
        self._load_themed(f'ultrarare_{item_suffix}', 
                         os.path.join("sprites", f"ultrarare_{item_suffix}.png"), 
                         target_size=(110, 110))
        
        # Load bad item
        self._load_themed(f'bad_item_{theme}', 
                         os.path.join("sprites", f"bad_item_{theme}.png"), 
                         target_size=(110, 110))
        
        # --- WISH VIDEOS (Shared) ---
        self._load_video('wish_granted', os.path.join("videos", "wish_granted.mov"))
        self._load_video('no_wish', os.path.join("videos", "no_wish.mov"))
        
        # --- LOAD ALL CATEGORY SPRITES FOR UI FALLING ITEMS (Option A) ---
        # This loads sprites from ALL themes so menus can show variety
        # Memory cost: ~580KB total for 12 sprites (110x110 each)
        log("[AssetManager] Loading cross-category sprites for UI...")
        
        # Food category (uses 'item' suffix)
        for rarity in ['ultracommon', 'common', 'rare', 'ultrarare']:
            self._load_shared(f'food_{rarity}', 
                             os.path.join("food", "sprites", f"{rarity}_item.png"), 
                             target_size=(110, 110))
        
        # Culture category (uses 'item' suffix)
        for rarity in ['ultracommon', 'common', 'rare', 'ultrarare']:
            self._load_shared(f'culture_{rarity}', 
                             os.path.join("culture", "sprites", f"{rarity}_item.png"), 
                             target_size=(110, 110))
        
        # People category (uses 'book' suffix)
        for rarity in ['ultracommon', 'common', 'rare', 'ultrarare']:
            self._load_shared(f'people_{rarity}', 
                             os.path.join("people", "sprites", f"{rarity}_book.png"), 
                             target_size=(110, 110))
        
        # --- THEME-SPECIFIC PLAYER SPRITES ---
        self._load_themed('sprite_idle', os.path.join("sprites", "Sprite1.png"), target_size=(190, 320))
        self._load_themed('sprite_right', os.path.join("sprites", "Sprite_right.png"), target_size=(210, 340))
        self._load_themed('sprite_left', os.path.join("sprites", "Sprite_left.png"), target_size=(210, 340))
        
        # --- CORNER CHIBI ---
        self._load_themed('corner_chibi', os.path.join("sprites", "corner_chibi.png"), target_size=(150, 150))

        # --- HEALTH HEARTS ---
        for i in range(1, 7):
            self._load_shared(f'h{i}', os.path.join("sprites", f"H{i}.png"), target_size=(300, 100))
        
        # === PERLA ===
        self._load_shared('perla_default', os.path.join("sprites", "Perla (default).png"), (150, 150))
        
        # === AUDIO ===
        self._load_audio('click', os.path.join("audio", "Start (BUTTONSTART.mp3"))
        self._load_audio('good', os.path.join("audio", "Good item (mp3cut.net).mp3"))
        self._load_audio('bad', os.path.join("audio", "Bad item (mp3cut.net).mp3"))
        self._load_audio('minus_life', os.path.join("audio", "minus 1 (mp3cut.net).mp3"))
        self._load_audio('plus_score', os.path.join("audio", "plus 1 (mp3cut.net).mp3"))

               # === NEW SFX ===
        self._load_audio('wheel_spin', os.path.join("audio", "SPIN.mp3"))
        self._load_audio('button_click', os.path.join("audio", "BUTTONSTART.mp3"))
        self._load_audio('start_button_sfx', os.path.join("audio", "BUTTONSTART.mp3"))

        # === MUSIC ===
        theme = self.theme_manager.get_theme()
        log(f"[AssetManager] Setting up music for theme: {theme}")
        
        # Menu music (shared)
        menu_music = os.path.join(self.base_path, "audio", "MENU(FINAL).mp3")  # Default to PEOPLE theme music for menu
        log(f"[AssetManager] Looking for menu music at: {menu_music}")
        log(f"[AssetManager] Menu music exists: {os.path.exists(menu_music)}")
        
        # Theme-specific gameplay music
        if theme == 'food':
            ingame_music = os.path.join(self.base_path, "audio", "FOOD.mp3")
        elif theme == 'culture':
            ingame_music = os.path.join(self.base_path, "audio", "CULTURE.mp3")
        elif theme == 'people':
            ingame_music = os.path.join(self.base_path, "audio", "MENU(FINAL).mp3")
        else:
            ingame_music = os.path.join(self.base_path, "audio", "In game theme v2.mp3")
        
        log(f"[AssetManager] Looking for theme music at: {ingame_music}")
        log(f"[AssetManager] Theme music exists: {os.path.exists(ingame_music)}")
        
        # Fallbacks if files don't exist
        if not os.path.exists(menu_music):
            log(f"[AssetManager] FALLBACK: Using default menu music")
            menu_music = os.path.join(self.base_path, "audio", "Menu theme v3.mp3")
        if not os.path.exists(ingame_music):
            log(f"[AssetManager] FALLBACK: Using default ingame music for {theme}")
            ingame_music = os.path.join(self.base_path, "audio", "In game theme v2.mp3")
        
        log(f"[AssetManager] Final menu music: {os.path.basename(menu_music)}")
        log(f"[AssetManager] Final ingame music: {os.path.basename(ingame_music)}")
        
        self.music_paths = {
            'menu': menu_music,
            'ingame': ingame_music
        }
        
        if self.fallbacks_used:
            log(f"[AssetManager] Fallbacks used: {', '.join(self.fallbacks_used)}")
        
        log("[AssetManager] All assets loaded")
        return self
    
    def _load_themed(self, asset_name, relative_path, target_size=None):
        """
        Load from theme folder first, fallback to root.
        Looks in: assets/{theme}/filename.png
        """
        theme = self.theme_manager.get_theme()
        themed_full = os.path.join(self.base_path, theme, relative_path)
        
        if os.path.exists(themed_full):
            self.assets[asset_name] = self._load_image_file(themed_full, target_size)
            return
        
        # Fallback to root assets
        shared_full = os.path.join(self.base_path, relative_path)
        if os.path.exists(shared_full):
            log(f"[AssetManager] Fallback: {relative_path}")
            self.fallbacks_used.append(asset_name)
            self.assets[asset_name] = self._load_image_file(shared_full, target_size)
            return
        
        log(f"[AssetManager] Missing: {themed_full}")
        self.assets[asset_name] = None
    
    def _load_shared(self, asset_name, relative_path, target_size=None):
        """Load from root assets folder."""
        full_path = os.path.join(self.base_path, relative_path)
        self.assets[asset_name] = self._load_image_file(full_path, target_size)
        if self.assets[asset_name] is None:
            log(f"[AssetManager] Missing shared asset: {relative_path}")
    
    def _load_audio(self, sound_name, relative_path):
        """Load audio file."""
        full_path = os.path.join(self.base_path, relative_path)
        try:
            self.sounds[sound_name] = pygame.mixer.Sound(full_path)
        except:
            self.sounds[sound_name] = None
    
    def _load_image_file(self, full_path, target_size=None):
        """Load and scale image using smoothscale for high quality."""
        try:
            image = pygame.image.load(full_path).convert_alpha()
            if target_size:
                # Use smoothscale for better quality when downscaling
                image = pygame.transform.smoothscale(image, target_size)
            return image
        except Exception as e:
            log(f"[AssetManager] Error loading {full_path}: {e}")
            return None
        
    def _load_video(self, video_name, relative_path):
        """Store video path for playback."""
        full_path = os.path.join(self.base_path, relative_path)
        if os.path.exists(full_path):
            self.assets[video_name] = full_path
            log(f"[AssetManager] Loaded video: {relative_path}")
        else:
            log(f"[AssetManager] Video not found: {full_path}")
            self.assets[video_name] = None

    def get_video(self, name):
        """Get video path by key."""
        return self.assets.get(name)
    
    def get(self, name):
        """Get asset by key."""
        return self.assets.get(name)
    
    def get_sound(self, name):
        """Get sound by key."""
        return self.sounds.get(name)
    
    def get_theme_manager(self):
        """Get theme manager."""
        return self.theme_manager
    
    def play_music(self, music_type, loops=-1, fade_ms=500):
        """
        Play background music by type.
        music_type: 'menu' or 'ingame'
        """
        if music_type not in self.music_paths:
            log(f"[AssetManager] Unknown music type: {music_type}")
            return
        
        music_path = self.music_paths[music_type]
        
        if not os.path.exists(music_path):
            log(f"[AssetManager] Music file not found: {music_path}")
            return
        
        try:
            # Fade out current music if playing
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(300)
                pygame.time.wait(300)
            
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            log(f"[AssetManager] Playing {music_type} music: {os.path.basename(music_path)}")
        except Exception as e:
            log(f"[AssetManager] Error playing music: {e}")

    def switch_theme_music(self, new_theme):
        """Change music when switching themes mid-game."""
        if new_theme == 'food':
            music_file = "FOOD.mp3"
        elif new_theme == 'culture':
            music_file = "CULTURE.mp3"
        elif new_theme == 'people':
            music_file = "PEOPLE.mp3"
        else:
            music_file = "In game theme v2.mp3"
        
        new_path = os.path.join(self.base_path, "audio", "new_bg_music", music_file)
        
        if os.path.exists(new_path):
            self.music_paths['ingame'] = new_path
            self.play_music('ingame')
        else:
            log(f"[AssetManager] Theme music not found: {new_path}")