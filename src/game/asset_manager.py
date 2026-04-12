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
        self._load_shared('menu_button', os.path.join("ui", "menu_button2.png"))
        self._load_shared('title1', os.path.join("ui", "title1.png"))
        self._load_shared('title2', os.path.join("ui", "WAVE&WISH.png"))
        
        # --- GLOBAL EFFECTS (Glows) ---
        self._load_shared('common_glow', os.path.join("effects", "common_glow.png"), (130, 130))
        self._load_shared('rare_glow', os.path.join("effects", "rare_glow.png"), (130, 130))
        self._load_shared('ultra_rare_glow', os.path.join("effects", "ultra_rare_glow.png"), (130, 130))
        
        # --- SHARED START/END SCREEN BACKGROUND ---
        self._load_shared('start_background', os.path.join("backgrounds", "people_bg.png"), target_size=(1920, 1080))
        
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
        self._load_audio('click', os.path.join("audio", "Start (mp3cut.net).mp3"))
        self._load_audio('good', os.path.join("audio", "Good item (mp3cut.net).mp3"))
        self._load_audio('bad', os.path.join("audio", "Bad item (mp3cut.net).mp3"))
        self._load_audio('minus_life', os.path.join("audio", "minus 1 (mp3cut.net).mp3"))
        self._load_audio('plus_score', os.path.join("audio", "plus 1 (mp3cut.net).mp3"))
        
        # === MUSIC ===
        menu_music = os.path.join(self.base_path, "audio", "Menu theme v3.mp3")
        ingame_music = os.path.join(self.base_path, theme, "audio", "In game theme.mp3")
        if not os.path.exists(ingame_music):
            ingame_music = os.path.join(self.base_path, "audio", "In game theme v2.mp3")
        
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
    
    def get(self, name):
        """Get asset by key."""
        return self.assets.get(name)
    
    def get_sound(self, name):
        """Get sound by key."""
        return self.sounds.get(name)
    
    def get_theme_manager(self):
        """Get theme manager."""
        return self.theme_manager