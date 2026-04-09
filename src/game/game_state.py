import json
import os
from datetime import datetime

# game_state.py
class GameState:
    HIGHSCORE_FILE = "highscore.json"
    MAX_HIGH_SCORES = 5  # Keep top 5 scores
    
    def __init__(self, assets=None):
        self.assets = assets # Store assets to access sounds
        self.score = 0
        self.lives = 6  # Support H1-H6 sprites
        self.game_over = False
        self.high_scores = self._load_high_scores()
        self.high_score = self.high_scores[0]['score'] if self.high_scores else 0
    
    def _load_high_scores(self):
        try:
            if os.path.exists(self.HIGHSCORE_FILE):
                with open(self.HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_scores', [])
        except:
            pass
        return []
    
    def _save_high_scores(self):
        try:
            with open(self.HIGHSCORE_FILE, 'w') as f:
                json.dump({'high_scores': self.high_scores}, f, indent=2)
        except:
            pass
    
    def handle_caught(self, items):
        """Update score/lives AND play SFX."""
        for item in items:
            if item.type == 'good':
                self.score += 1
                # --- PLAY GOOD SOUND ---
                if self.assets and 'good' in self.assets.sounds:
                    self.assets.sounds['good'].play()
            else:
                self.lives -= 1
                # --- PLAY BAD SOUND ---
                if self.assets and 'bad' in self.assets.sounds:
                    self.assets.sounds['bad'].play()
    
    def handle_missed_good(self, count):
        """Reduce lives and play minus_life sound when a good item is missed."""
        if count > 0:
            self.lives -= count
            # --- PLAY LIFE LOST SOUND ---
            if self.assets and 'minus_life' in self.assets.sounds:
                self.assets.sounds['minus_life'].play()
    
    def check_game_over(self):
        if self.lives <= 0:
            # Prevent multiple triggers
            if not self.game_over:
                self.game_over = True
                self._add_high_score()
        return self.game_over
    
    def _add_high_score(self):
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
        for entry in self.high_scores:
            entry['is_new'] = False
        
        self.score = 0
        self.lives = 6
        self.game_over = False

    def is_new_high_score(self):
        if self.high_scores and self.game_over:
            return self.high_scores[0].get('is_new', False)
        return False