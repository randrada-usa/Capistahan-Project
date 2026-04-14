"""
theme_manager.py
Central theme configuration for Capiztahan Gacha Game.
Rey - Architecture Module

Handles 3-category system: 'food', 'culture', 'people'
"""

import os


class ThemeManager:
    """
    Manages the active theme category and resolves asset paths.
    
    Themes:
        - 'food': Food category assets (local dishes, ingredients)
        - 'culture': Culture category assets (traditions, festivals)
        - 'people': People category assets (local figures, community)
    """
    
    VALID_THEMES = ['food', 'culture', 'people']
    DEFAULT_THEME = 'food'
    
    def __init__(self, theme='food'):
        self._theme = self.DEFAULT_THEME
        self.set_theme(theme)
        
        # Assets that are THEME-SPECIFIC (change per category)
        self.themed_assets = [
            'background',
            'good_item',      # The "catchable" good items
            'bad_item',       # The "avoid" items
            'sprite_idle',    # Player mascot expressions
            'sprite_right',
            'sprite_left',
            'corner_chibi',   # Corner reaction character
            # Add more here if needed
        ]
        
        # Assets that are SHARED across all themes (UI, audio, hearts)
        self.shared_assets = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Health sprites
            'start_button',
            'retry_button', 
            'menu_button',
            'title1',
            'title2',
        ]
    
    def set_theme(self, theme):
        """Validate and set the active theme."""
        theme = theme.lower().strip()
        if theme in self.VALID_THEMES:
            self._theme = theme
            print(f"[ThemeManager] Theme set to: {theme.upper()}")
        else:
            print(f"[ThemeManager] Invalid theme '{theme}', using default: {self.DEFAULT_THEME}")
            self._theme = self.DEFAULT_THEME
    
    def get_theme(self):
        """Return current theme string."""
        return self._theme
    
    def resolve_path(self, relative_path, asset_name=None):
        """
        Resolve asset path based on whether it's themed or shared.
        
        Args:
            relative_path: Original path from AssetManager
            asset_name: Key name of the asset (to check if themed)
        
        Returns:
            str: Path with theme folder inserted if applicable
        """
        if asset_name and asset_name in self.themed_assets:
            # FIXED: Use os.path.split instead of string split for cross-platform
            # Insert theme folder: assets/background.png → assets/food/background.png
            parts = relative_path.split(os.sep)
            # Also handle forward slashes in case they were hardcoded
            if len(parts) == 1:
                parts = relative_path.split('/')
            
            if len(parts) >= 2 and parts[0] == 'assets':
                # Insert theme after 'assets'
                themed_path = os.path.join(parts[0], self._theme, *parts[1:])
                return themed_path
        
        # Shared asset or unknown - use original path
        return relative_path
    
    def is_themed(self, asset_name):
        """Check if an asset should vary by theme."""
        return asset_name in self.themed_assets
    
    def get_theme_display_name(self):
        """Return human-readable theme name for UI."""
        names = {
            'food': 'Capiz Cuisine',
            'culture': 'Capiz Traditions', 
            'people': 'Capiz Community'
        }
        return names.get(self._theme, 'Unknown')