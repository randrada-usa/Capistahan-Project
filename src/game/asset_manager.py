"""
Asset Manager - Loads and scales sprites and audio for the BreadRush project.
MODIFIED FOR CAPIZTAHAN: Theme-aware loading with fallback support.
PyInstaller-ready with safe logging.
"""

import pygame
import os
import sys


def resource_path(relative_path):
    """ 
    Get absolute path to resource, works for dev and PyInstaller.
    Returns path to the 'assets' folder, so don't prepend 'assets/' again.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")
    
    # Return the assets folder directly
    return os.path.join(base_path, "assets")


def log(msg):
    """Print messages only in development mode, not in EXE"""
    if not getattr(sys, 'frozen', False):
        print(msg)


# Import the new ThemeManager
from src.game.theme_manager import ThemeManager


class AssetManager:
    """
    Centralized asset loading with automatic scaling, error handling,
    and THEME SUPPORT for Capiztahan Gacha system.
    """
    
    def __init__(self, theme='food'):
        self.assets = {}
        self.sounds = {}        
        self.music_paths = {}
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(theme)
        self.base_path = resource_path("")  # Already points to assets folder
        
        # Ensure mixer is initialized (for test environments)
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                log(f"[AssetManager] Mixer init failed: {e}")
        
        # Track which assets failed to load themed version (for debugging)
        self.fallbacks_used = []
        
    def load_all(self):
        """
        Load and scale all game assets based on the active theme.
        Shared assets load from /assets/, themed assets from /assets/{theme}/
        """
        theme = self.theme_manager.get_theme()
        log(f"[AssetManager] Loading assets for theme: {theme}")
        log(f"[AssetManager] Base path: {self.base_path}")

        # --- WHEEL SCREEN ASSETS (Shared) ---
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

        self._load_shared('start_button', os.path.join("ui", "start_button.png"))
        self._load_shared('retry_button', os.path.join("ui", "retry_button.png"))
        self._load_shared('menu_button', os.path.join("ui", "menu_button.png"))
        self._load_shared('title1', os.path.join("ui", "title1.png"))
        self._load_shared('title2', os.path.join("ui", "title2.png"))

        # --- SFX (Shared across themes) ---
        self._load_shared_audio('click', os.path.join("audio", "Start (mp3cut.net).mp3"))
        self._load_shared_audio('good', os.path.join("audio", "Good item (mp3cut.net).mp3"))
        self._load_shared_audio('bad', os.path.join("audio", "Bad item (mp3cut.net).mp3"))
        self._load_shared_audio('minus_life', os.path.join("audio", "minus 1 (mp3cut.net).mp3"))
        self._load_shared_audio('plus_score', os.path.join("audio", "plus 1 (mp3cut.net).mp3"))
        
        # Rarity SFX
        self._load_shared_audio('rare_catch', os.path.join("audio", "rare_catch.mp3"))
        self._load_shared_audio('ultra_catch', os.path.join("audio", "ultra_catch.mp3"))

        # --- MUSIC (Themed per category) ---
        # Menu music stays shared
        menu_music_path = os.path.join(self.base_path, "audio", "Menu theme v3.mp3")
        
        # Ingame music is themed: assets/food/audio/In game theme.mp3
        themed_music_dir = os.path.join(self.base_path, theme, "audio")
        ingame_music_path = os.path.join(themed_music_dir, "In game theme.mp3")
        
        # Fallback to shared if themed music doesn't exist
        if not os.path.exists(ingame_music_path):
            ingame_music_path = os.path.join(self.base_path, "audio", "In game theme v2.mp3")
        
        self.music_paths = {
            'menu': menu_music_path,
            'ingame': ingame_music_path
        }

        # Log summary
        if self.fallbacks_used:
            log(f"[AssetManager] Fallbacks used for: {', '.join(self.fallbacks_used)}")
        
        log(f"[AssetManager] All assets loaded")
        return self
    
    def _load_themed(self, asset_name, relative_path, target_size=None):
        """
        Load a theme-specific asset with fallback to shared folder.
        Tries: assets/{theme}/path → assets/path → error placeholder
        """
        theme = self.theme_manager.get_theme()
        themed_full = os.path.join(self.base_path, theme, relative_path)
        
        # Try themed version first
        if os.path.exists(themed_full):
            log(f"[AssetManager] Loading themed: {theme}/{relative_path}")
            self.assets[asset_name] = self._load_image_file(themed_full, target_size)
            return
        
        # Fallback to shared/default version
        shared_full = os.path.join(self.base_path, relative_path)
        if os.path.exists(shared_full):
            log(f"[AssetManager] Themed asset missing, using fallback: {relative_path}")
            self.fallbacks_used.append(asset_name)
            self.assets[asset_name] = self._load_image_file(shared_full, target_size)
            return
        
        # Total failure - placeholder
        log(f"[AssetManager] ERROR: Asset not found: {themed_full} or {shared_full}")
        self.assets[asset_name] = self._create_placeholder(target_size)
    
    def _load_shared(self, asset_name, relative_path, target_size=None):
        """Load a shared asset (not theme-dependent) from root assets/."""
        full_path = os.path.join(self.base_path, relative_path)
        log(f"[AssetManager] Loading shared: {relative_path}")
        self.assets[asset_name] = self._load_image_file(full_path, target_size)
    
    def _load_shared_audio(self, sound_name, relative_path):
        """Load audio (always shared across themes)."""
        full_path = os.path.join(self.base_path, relative_path)
        log(f"[AssetManager] Loading audio: {relative_path}")
        self.sounds[sound_name] = self._load_sound_file(full_path)
    
    def _load_image_file(self, full_path, target_size=None):
        """Actual file loading with error handling."""
        try:
            image = pygame.image.load(full_path).convert_alpha()
            if target_size:
                image = pygame.transform.smoothscale(image, target_size)
            return image
        except Exception as e:
            log(f"[AssetManager] Error loading {full_path}: {e}")
            return self._create_placeholder(target_size)
    
    def _load_sound_file(self, full_path):
        """Actual sound loading with error handling."""
        try:
            return pygame.mixer.Sound(full_path)
        except Exception as e:
            log(f"[AssetManager] Error loading sound {full_path}: {e}")
            # FIXED: Return None instead of invalid buffer
            return None
    
    def _create_placeholder(self, target_size):
        """Create magenta error placeholder surface."""
        surf = pygame.Surface(target_size or (100, 100), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 128))
        return surf

    def get(self, name):
        """Retrieve a loaded asset."""
        return self.assets.get(name)
    
    def get_theme_manager(self):
        """Access theme manager for theme info/display."""
        return self.theme_manager
    
    def change_theme(self, new_theme):
        """
        Runtime theme switching (for development/testing).
        """
        self.theme_manager.set_theme(new_theme)
        self.assets.clear()
        self.sounds.clear()
        self.music_paths.clear()
        return self.load_all()