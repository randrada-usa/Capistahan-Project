"""
game_state.py
Scoring, lives, and high score management for Capiztahan Gacha Game.
MODIFIED: Time-based mode, rarity scoring, corner chibi reactions.
"""

import json
import os
from datetime import datetime


class GameState:
    HIGHSCORE_FILE = "highscore.json"
    MAX_HIGH_SCORES = 5  # Keep top 5 scores
    
    # RARITY POINT VALUES (for Gio's gacha system)
    RARITY_POINTS = {
        'common': 1,
        'rare': 3,
        'ultra': 5
    }
    
    def __init__(self, assets=None):
        self.assets = assets  # Store assets to access sounds
        self.score = 0
        self.lives = 6  # Support H1-H6 sprites
        self.game_over = False
        self.high_scores = self._load_high_scores()
        self.high_score = self.high_scores[0]['score'] if self.high_scores else 0
        
        # Time-based mode tracking
        self.time_remaining = 60.0  # Seconds (set by Game.reset_game)
        self.max_time = 60.0
        
        # Corner chibi reaction tracking (for Jen's UI)
        self.last_catch_rarity = None  # 'common', 'rare', 'ultra', or None
        self.reaction_timer = 0.0  # How long to show reaction (seconds)
        self.reaction_duration = 1.0  # Show reaction for 1 second
    
    def _load_high_scores(self):
        """Load high scores from JSON file."""
        try:
            if os.path.exists(self.HIGHSCORE_FILE):
                with open(self.HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_scores', [])
        except Exception as e:
            print(f"[GameState] Error loading high scores: {e}")
        return []
    
    def _save_high_scores(self):
        """Save high scores to JSON file."""
        try:
            with open(self.HIGHSCORE_FILE, 'w') as f:
                json.dump({'high_scores': self.high_scores}, f, indent=2)
        except Exception as e:
            print(f"[GameState] Error saving high scores: {e}")
    
    def update_timer(self, dt):
        """
        Update countdown timer for time-based mode.
        Call this every frame from main game loop.
        """
        if self.game_over:
            return
            
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0
            self.trigger_game_over()
        
        # Update reaction timer for corner chibi
        if self.reaction_timer > 0:
            self.reaction_timer -= dt
            if self.reaction_timer <= 0:
                self.last_catch_rarity = None
    
    def trigger_game_over(self):
        """Force game over (for time-based mode or manual trigger)."""
        if not self.game_over:
            self.game_over = True
            self._add_high_score()
            print(f"[GameState] Game Over! Final Score: {self.score}")
    
    def handle_caught(self, items):
        """
        Update score/lives AND play SFX based on item rarity.
        
        Args:
            items: List of caught items (from falling_objects.py)
                   Each item should have .type ('good'/'bad') and .rarity attribute
        """
        for item in items:
            if item.type == 'good':
                # RARITY-BASED SCORING
                rarity = getattr(item, 'rarity', 'common')  # Default to common
                points = self.RARITY_POINTS.get(rarity, 1)
                self.score += points
                
                # Track for corner chibi reaction (Jen's UI)
                self.last_catch_rarity = rarity
                self.reaction_timer = self.reaction_duration
                
                # Play appropriate SFX based on rarity
                self._play_rarity_sfx(rarity)
                
            else:
                # Bad item - lose life
                self.lives -= 1
                self.last_catch_rarity = 'bad'
                self.reaction_timer = self.reaction_duration
                
                # Play bad sound
                if self.assets and 'bad' in self.assets.sounds:
                    self.assets.sounds['bad'].play()
    
    def _play_rarity_sfx(self, rarity):
        """Play sound effect based on item rarity."""
        if not self.assets:
            return
            
        if rarity == 'ultra' and 'ultra_catch' in self.assets.sounds:
            self.assets.sounds['ultra_catch'].play()
        elif rarity == 'rare' and 'rare_catch' in self.assets.sounds:
            self.assets.sounds['rare_catch'].play()
        elif 'good' in self.assets.sounds:
            # Fallback to common good sound
            self.assets.sounds['good'].play()
    
    def handle_missed_good(self, count):
        """Reduce lives and play minus_life sound when a good item is missed."""
        if count > 0:
            self.lives -= count
            # Play life lost sound
            if self.assets and 'minus_life' in self.assets.sounds:
                self.assets.sounds['minus_life'].play()
    
    def check_game_over(self):
        """Check if lives depleted (traditional mode) or time expired."""
        if self.lives <= 0 and not self.game_over:
            self.game_over = True
            self._add_high_score()
        return self.game_over
    
    def _add_high_score(self):
        """Add current score to high score list if worthy."""
        if self.score > 0:
            entry = {
                'score': self.score,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'is_new': True 
            }
            self.high_scores.append(entry)
            self.high_scores.sort(key=lambda x: x['score'], reverse=True)
            self.high_scores = self.high_scores[:self.MAX_HIGH_SCORES]
            self.high_score = self.high_scores[0]['score']
            self._save_high_scores()
    
    def reset(self):
        """Reset for new game round."""
        # Clear 'is_new' flags from previous game
        for entry in self.high_scores:
            entry['is_new'] = False
        
        self.score = 0
        self.lives = 6
        self.game_over = False
        self.time_remaining = self.max_time
        self.last_catch_rarity = None
        self.reaction_timer = 0.0
    
    def is_new_high_score(self):
        """Check if current game achieved a new high score."""
        if self.high_scores and self.game_over:
            return self.high_scores[0].get('is_new', False)
        return False
    
    def get_reaction_state(self):
        """
        Get current corner chibi reaction state for Jen's UI.
        
        Returns:
            tuple: (rarity_type, progress_0_to_1) or (None, 0) if no reaction
        """
        if self.reaction_timer <= 0 or self.last_catch_rarity is None:
            return None, 0.0
        
        progress = self.reaction_timer / self.reaction_duration
        return self.last_catch_rarity, progress
    
    def get_formatted_time(self):
        """Return time remaining as formatted string (MM:SS)."""
        total_seconds = int(self.time_remaining)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"