"""
asset_manager.py
Capiztahan Gacha Game - Asset Manager
Loads and caches all game assets for a given theme.
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

        # === WHEEL SCREEN ASSETS (Shared UI) ===
        self._load_shared('wheel_base', os.path.join("ui", "wheel.png"))
        # Increased icon size from 100 to 140
        self._load_shared('perla_food', os.path.join("ui", "perla_food.png"), target_size=(285, 285))
        self._load_shared('perla_culture', os.path.join("ui", "perla_culture.png"), target_size=(285, 285))
        self._load_shared('perla_people', os.path.join("ui", "perla_people.png"), target_size=(285, 285))
        
        # --- THEME-SPECIFIC BACKGROUNDS ---
        self._load_themed('background', 
            os.path.join("backgrounds", "background.png"), 
            target_size=(1920, 1080))
        
        # --- THEME-SPECIFIC PLAYER SPRITES ---
        self._load_themed('sprite_idle',
            os.path.join("sprites", "Sprite1.png"),
            target_size=(190, 320))
        self._load_themed('sprite_right',
            os.path.join("sprites", "Sprite_right.png"),
            target_size=(210, 340))
        self._load_themed('sprite_left',
            os.path.join("sprites", "Sprite_left.png"),
            target_size=(210, 340))
        
        # --- CORNER CHIBI (New for Capiztahan) ---
        self._load_themed('corner_chibi',
            os.path.join("sprites", "corner_chibi.png"),
            target_size=(150, 150))

        # --- THEME-SPECIFIC ITEMS ---
        self._load_themed('good_item',
            os.path.join("sprites", "Good item.png"),
            target_size=(100, 100))
        self._load_themed('bad_item',
            os.path.join("sprites", "Bad item.png"), 
            target_size=(100, 100))

        # --- SHARED UI ASSETS (always from root assets/) ---
        self._load_shared('h1', os.path.join("sprites", "H1.png"), target_size=(300, 100))
        self._load_shared('h2', os.path.join("sprites", "H2.png"), target_size=(300, 100))
        self._load_shared('h3', os.path.join("sprites", "H3.png"), target_size=(300, 100))
        self._load_shared('h4', os.path.join("sprites", "H4.png"), target_size=(300, 100))
        self._load_shared('h5', os.path.join("sprites", "H5.png"), target_size=(300, 100))
        self._load_shared('h6', os.path.join("sprites", "H6.png"), target_size=(300, 100))

        log(f"[AssetManager] Loading theme: {theme}")
        
        # === SPECIFIC FOOD ITEMS (from assets/food/) ===
        # These are loaded as: Stick_O, Isaw, Puto, Dynamite, BadItem
        food_items = {
            'Stick_O': (100, 100),  # Ultra Rare
            'Isaw': (100, 100),     # Rare
            'Puto': (100, 100),     # Common
            'Dynamite': (100, 100), # Very Common
            'BadItem': (100, 100)   # Bad items
        }
        
        for item_name, size in food_items.items():
            # Loads from: assets/food/Stick_O.png, etc.
            self._load_themed(item_name, f"{item_name}.png", target_size=size)
        
        # === GLOW EFFECTS (from assets/sprites/) ===
        self._load_shared('common_glow', os.path.join("sprites", "Common_glow.png"), (120, 120))
        self._load_shared('rare_glow', os.path.join("sprites", "Rare_glow.png"), (120, 120))
        self._load_shared('ultrarare_glow', os.path.join("sprites", "Ultrarare_glow.png"), (120, 120))
        
        # === PERLA (from assets/sprites/) ===
        self._load_shared('perla_default', os.path.join("sprites", "Perla (default).png"), (150, 150))
        # Optional expressions (silent fail if missing)
        for expr in ['happy', 'excited', 'sad']:
            try:
                self._load_shared(f'perla_{expr}', os.path.join("sprites", f"Perla ({expr}).png"), (150, 150))
            except:
                pass
        
        # === BACKGROUND (from assets/food/background/food_bg.png) ===
        self._load_background()
        
        # === PLAYER SPRITES ===
        self._load_themed('sprite_idle', os.path.join("sprites", "Sprite1.png"), (190, 320))
        self._load_themed('sprite_right', os.path.join("sprites", "Sprite_right.png"), (210, 340))
        self._load_themed('sprite_left', os.path.join("sprites", "Sprite_left.png"), (210, 340))
        
        # === HEALTH HEARTS ===
        for i in range(1, 7):
            self._load_shared(f'h{i}', os.path.join("sprites", f"H{i}.png"), (300, 100))
        
        # === UI BUTTONS ===
        self._load_shared('start_button', os.path.join("ui", "start_button.png"))
        self._load_shared('retry_button', os.path.join("ui", "retry_button.png"))
        self._load_shared('menu_button', os.path.join("ui", "menu_button.png"))
        self._load_shared('title1', os.path.join("ui", "title1.png"))
        self._load_shared('title2', os.path.join("ui", "title2.png"))
        
        # === AUDIO ===
        self._load_audio('click',      os.path.join("audio", "Start (mp3cut.net).mp3"))
        self._load_audio('good',       os.path.join("audio", "Good item (mp3cut.net).mp3"))
        self._load_audio('bad',        os.path.join("audio", "Bad item (mp3cut.net).mp3"))
        self._load_audio('minus_life', os.path.join("audio", "minus 1 (mp3cut.net).mp3"))
        self._load_audio('plus_score', os.path.join("audio", "plus 1 (mp3cut.net).mp3"))

        # === MUSIC PATHS ===
        menu_music   = os.path.join(self.base_path, "audio", "Menu theme v3.mp3")
        ingame_music = os.path.join(self.base_path, theme, "audio", "In game theme.mp3")
        if not os.path.exists(ingame_music):
            ingame_music = os.path.join(self.base_path, "audio", "In game theme v2.mp3")

        self.music_paths = {
            'menu':   menu_music,
            'ingame': ingame_music
        }

        if self.fallbacks_used:
            log(f"[AssetManager] Fallbacks used: {', '.join(self.fallbacks_used)}")

        log("[AssetManager] All assets loaded")
        return self
    
    def _load_background(self):
        """Load themed background from assets/{theme}/background/{theme}_bg.png."""
        theme = self.theme_manager.get_theme()
        
        # Specific path: assets/food/background/food_bg.png
        themed_bg = os.path.join(self.base_path, theme, "background", f"{theme}_bg.png")
        
        if os.path.exists(themed_bg):
            log(f"[AssetManager] Loading background: {theme}/background/{theme}_bg.png")
            self.assets['background'] = self._load_image_file(themed_bg, (1920, 1080))
        else:
            log(f"[AssetManager] Background not found: {themed_bg}")
            self.assets['background'] = None
    
    def _load_themed(self, asset_name, relative_path, target_size=None):
        """Load from assets/{theme}/ first, fallback to assets/."""
        theme = self.theme_manager.get_theme()
        themed_full = os.path.join(self.base_path, theme, relative_path)

        if os.path.exists(themed_full):
            self.assets[asset_name] = self._load_image_file(themed_full, target_size)
            return

        shared_full = os.path.join(self.base_path, relative_path)
        if os.path.exists(shared_full):
            log(f"[AssetManager] Fallback: {relative_path}")
            self.fallbacks_used.append(asset_name)
            self.assets[asset_name] = self._load_image_file(shared_full, target_size)
            return
        
        # Not found
        log(f"[AssetManager] Missing: {themed_full}")
        self.assets[asset_name] = None

    def _load_shared(self, asset_name, relative_path, target_size=None):
        """Load from root assets/ folder."""
        full_path = os.path.join(self.base_path, relative_path)
        self.assets[asset_name] = self._load_image_file(full_path, target_size)
    
    def _load_audio(self, sound_name, relative_path):
        """Load a sound effect."""
        full_path = os.path.join(self.base_path, relative_path)
        try:
            self.sounds[sound_name] = pygame.mixer.Sound(full_path)
        except Exception:
            self.sounds[sound_name] = None

    def _load_image_file(self, full_path, target_size=None):
        """Load and optionally scale an image."""
        try:
            image = pygame.image.load(full_path).convert_alpha()
            if target_size:
                image = pygame.transform.smoothscale(image, target_size)
            return image
        except Exception as e:
            log(f"[AssetManager] Error loading {full_path}: {e}")
            return None

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def get(self, name):
        """Get an image asset by key."""
        return self.assets.get(name)

    def get_sound(self, name):
        """Get a sound asset by key."""
        return self.sounds.get(name)
    
    def get_theme_manager(self):
        """Get theme manager."""
        return self.theme_manager