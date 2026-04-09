"""
Asset Manager - Loads and scales sprites and audio for the BreadRush project.
PyInstaller-ready with safe logging.
"""

import pygame
import os
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def log(msg):
    """Print messages only in development mode, not in EXE"""
    if not getattr(sys, 'frozen', False):
        print(msg)


class AssetManager:
    """Centralized asset loading with automatic scaling and error handling."""
    
    def __init__(self):
        self.assets = {}
        self.sounds = {}        
        self.music_paths = {}
        self.base_path = resource_path("assets")
        
    def load_all(self):
        """Load and scale all game assets based on the production file tree."""
        
        # --- Backgrounds ---
        self.assets['background'] = self._load_image(
            os.path.join("backgrounds", "background.png"), 
            target_size=(1920, 1080)
        )
        
        # --- Player Sprites ---
        self.assets['sprite_idle'] = self._load_image(
            os.path.join("sprites", "Sprite1.png"),
            target_size=(190, 320)
        )
        self.assets['sprite_right'] = self._load_image(
            os.path.join("sprites", "Sprite_right.png"),
            target_size=(210, 340)
        )
        self.assets['sprite_left'] = self._load_image(
            os.path.join("sprites", "Sprite_left.png"),
            target_size=(210, 340)
        )

        # --- Items ---
        self.assets['good_item'] = self._load_image(
            os.path.join("sprites", "Good item.png"),
            target_size=(100, 100)
        )
        self.assets['bad_item'] = self._load_image(
            os.path.join("sprites", "Bad item.png"), 
            target_size=(100, 100)
        )

        # --- Health Sprites (H1 - H6) ---
        for i in range(1, 7):
            self.assets[f'h{i}'] = self._load_image(
                os.path.join("sprites", f"H{i}.png"),
                target_size=(300, 100)
            )

        # --- UI Assets ---
        self.assets['start_button'] = self._load_image(os.path.join("ui", "start_button.png"))
        self.assets['retry_button'] = self._load_image(os.path.join("ui", "retry_button.png"))
        self.assets['menu_button'] = self._load_image(os.path.join("ui", "menu_button.png"))
        self.assets['title1'] = self._load_image(os.path.join("ui", "title1.png"))
        self.assets['title2'] = self._load_image(os.path.join("ui", "title2.png"))

        # --- Audio ---
        self.sounds['click'] = self._load_sound(os.path.join("audio", "Start (mp3cut.net).mp3"))
        self.sounds['good'] = self._load_sound(os.path.join("audio", "Good item (mp3cut.net).mp3"))
        self.sounds['bad'] = self._load_sound(os.path.join("audio", "Bad item (mp3cut.net).mp3"))
        self.sounds['minus_life'] = self._load_sound(os.path.join("audio", "minus 1 (mp3cut.net).mp3"))
        self.sounds['plus_score'] = self._load_sound(os.path.join("audio", "plus 1 (mp3cut.net).mp3"))

        audio_dir = os.path.join(self.base_path, "audio")
        self.music_paths = {
            'menu': os.path.join(audio_dir, "Menu theme v3.mp3"),
            'ingame': os.path.join(audio_dir, "In game theme v2.mp3")
        }

        log(f"[AssetManager] All assets loaded from: {self.base_path}")
        return self
    
    def _load_image(self, relative_path, target_size=None):
        """Load image using the resource_path wrapper."""
        full_path = os.path.join(self.base_path, relative_path)
        try:
            image = pygame.image.load(full_path).convert_alpha()
            if target_size:
                image = pygame.transform.smoothscale(image, target_size)
            return image
        except Exception as e:
            log(f"[AssetManager] Error loading {full_path}: {e}")
            surf = pygame.Surface(target_size or (100, 100), pygame.SRCALPHA)
            surf.fill((255, 0, 255, 128))  # Magenta error color
            return surf

    def _load_sound(self, relative_path):
        """Load sound using the resource_path wrapper."""
        full_path = os.path.join(self.base_path, relative_path)
        try:
            return pygame.mixer.Sound(full_path)
        except Exception as e:
            log(f"[AssetManager] Error loading sound {full_path}: {e}")
            # Return silent sound instead of crashing
            return pygame.mixer.Sound(buffer=bytes(0))

    def get(self, name):
        """Retrieve a loaded asset."""
        return self.assets.get(name)