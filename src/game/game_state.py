"""
game_state.py - MODIFIED FOR CAPIZTAHAN
Added: Event system for Jen's player expressions
Keeps: Original score/lives management
"""

import json
import os
from datetime import datetime
from enum import Enum

# Import Rarity from falling_objects to avoid duplication
from src.game.falling_objects import Rarity
from src.game.wish_system import WishSystem


class GameState:
    HIGHSCORE_FILE = "highscore.json"
    MAX_HIGH_SCORES = 5
    
    # Wish system threshold
    WISH_THRESHOLD = 200
    
    # Category multipliers (tune these based on difficulty)
    CATEGORY_MULTIPLIERS = {
        'food': 1.0,
        'culture': 1.2,
        'people': 1.5
    }
    
    def __init__(self, assets=None, theme_manager=None):
        self.assets = assets
        self.theme_manager = theme_manager
        
        # Get category from ThemeManager
        if theme_manager:
            self.category = theme_manager.get_theme()
        else:
            self.category = 'food'
        
        self.multiplier = self.CATEGORY_MULTIPLIERS.get(self.category, 1.0)
        
        # Core stats
        self.score = 0
        self.lives = 6
        self.game_over = False
        
        # Session tracking
        self.session_best_catch = None
        self.catches_by_rarity = {
            'very_common': 0,
            'common': 0,
            'rare': 0,
            'ultra_rare': 0
    }
        
        # Events for Jen (cleared each frame)
        self.catch_events = {
            'rare_caught': False,
            'ultra_rare_caught': False,
            'combo_active': False,
            'milestone_reached': False
        }
        self._event_queue = []
        
        # FIXED: Track last milestone to detect crossings properly
        self._last_milestone = 0
        
        # Initialize wish system with category
        self.wish_system = WishSystem(category=self.category)
        
        # High scores
        self.high_scores = self._load_high_scores()
        self.high_score = self.high_scores[0]['score'] if self.high_scores else 0
    
    def _load_high_scores(self):
        try:
            if os.path.exists(self.HIGHSCORE_FILE):
                with open(self.HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_scores', [])
        except Exception as e:
            print(f"[GameState] Error loading high scores: {e}")
        return []
    
    def _save_high_scores(self):
        try:
            with open(self.HIGHSCORE_FILE, 'w') as f:
                json.dump({'high_scores': self.high_scores}, f, indent=2)
        except Exception as e:
            print(f"[GameState] Error saving high scores: {e}")
    
    def _trigger_event(self, event_name, data=None):
        """Queue event for Jen's UI to consume."""
        self.catch_events[event_name] = True
        self._event_queue.append({
            'type': event_name,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def consume_events(self):
        """Call this each frame in game_loop to get events for Jen."""
        events = self._event_queue.copy()
        self._event_queue.clear()
        
        # Reset one-shot flags
        self.catch_events['rare_caught'] = False
        self.catch_events['ultra_rare_caught'] = False
        self.catch_events['milestone_reached'] = False
        
        return events
    
    def get_events_for_jen(self):
        """Read-only peek at current events (for UI rendering)."""
        return self.catch_events.copy()
    
    def handle_caught(self, items):
        """Process caught items with rarity-based scoring."""
        for item in items:
            if item.type == 'good':
                # Base points from item rarity
                base_points = item.get_score_value()
                
                # Apply category multiplier
                points = int(base_points * self.multiplier)
                
                # FIXED: Check milestone BEFORE adding score to detect threshold crossing
                old_score = self.score
                self.score += points
                
                # In handle_caught, update the tracking line:
                rarity_key = item.rarity.value  # This now includes 'very_common'
                self.catches_by_rarity[rarity_key] += 1
                
                # Track best single catch
                catch_desc = f"{rarity_key.replace('_', ' ').title()} {self.category.title()}"
                if (not self.session_best_catch or 
                    base_points > self.session_best_catch['base_points']):
                    self.session_best_catch = {
                        'description': catch_desc,
                        'base_points': base_points,
                        'total_points': points
                    }
                
                # Fire rarity events for Jen - compare Enum to Enum
                if item.rarity == Rarity.RARE:
                    self._trigger_event('rare_caught', {
                        'points': points,
                        'description': catch_desc
                    })
                    if self.assets and 'plus_score' in self.assets.sounds:
                        self.assets.sounds['plus_score'].play()
                
                elif item.rarity == Rarity.ULTRA_RARE:
                    self._trigger_event('ultra_rare_caught', {
                        'points': points,
                        'description': catch_desc
                    })
                    if self.assets and 'good' in self.assets.sounds:
                        self.assets.sounds['good'].play()
                else:
                    if self.assets and 'good' in self.assets.sounds:
                        self.assets.sounds['good'].play()
                
                # FIXED: Milestone detection - check if we crossed any 50-point threshold
                old_milestone = old_score // 50
                new_milestone = self.score // 50
                if new_milestone > old_milestone and self.score > 0:
                    self._trigger_event('milestone_reached', {'score': self.score})
                    self._last_milestone = new_milestone * 50
                
            else:
                self.lives -= 1
                if self.assets and 'bad' in self.assets.sounds:
                    self.assets.sounds['bad'].play()
    
    def handle_missed_good(self, count):
        """Reduce lives when good items fall off screen."""
        if count > 0:
            self.lives -= count
            if self.assets and 'minus_life' in self.assets.sounds:
                self.assets.sounds['minus_life'].play()
    
    def check_game_over(self):
        if self.lives <= 0 and not self.game_over:
            self.game_over = True
            self._add_high_score()
        return self.game_over
    
    def trigger_game_over(self):
        """Called by timer running out"""
        if not self.game_over:
            self.game_over = True
            self._add_high_score()
    
    def _add_high_score(self):
        if self.score > 0:
            entry = {
                'score': self.score,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'is_new': True,
                'category': self.category,
                'category_display': self.theme_manager.get_theme_display_name() if self.theme_manager else 'Capiz Cuisine',
                'best_catch': self.session_best_catch['description'] if self.session_best_catch else None,
                'catches': self.catches_by_rarity.copy(),
                'multiplier': self.multiplier
            }
            self.high_scores.append(entry)
            self.high_scores.sort(key=lambda x: x['score'], reverse=True)
            self.high_scores = self.high_scores[:self.MAX_HIGH_SCORES]
            self.high_score = self.high_scores[0]['score']
            self._save_high_scores()
    
    def is_wish_eligible(self):
        """Check if player earned enough points to make a wish."""
        return self.score >= self.WISH_THRESHOLD
    
    def get_wish_status(self):
        """Returns dict for end screen progress bar."""
        return {
            'eligible': self.is_wish_eligible(),
            'threshold': self.WISH_THRESHOLD,
            'current': self.score,
            'progress_percent': min(100.0, (self.score / self.WISH_THRESHOLD) * 100)
        }
    
    def resolve_wish(self):
        """Called by end screen when player clicks 'Make Wish'."""
        return self.wish_system.roll_wish(self.score)
    
    def reset(self):
        """Reset for new game round."""
        for entry in self.high_scores:
            entry['is_new'] = False
        
        self.score = 0
        self.lives = 6
        self.game_over = False
        self.session_best_catch = None
        self.catches_by_rarity = {'common': 0, 'rare': 0, 'ultra_rare': 0}
        self.catch_events = {k: False for k in self.catch_events}
        self._event_queue.clear()
        self._last_milestone = 0  # FIXED: Reset milestone tracker
        
        # Re-initialize wish system for new category
        if self.theme_manager:
            self.category = self.theme_manager.get_theme()
        self.wish_system = WishSystem(category=self.category)
    
    def is_new_high_score(self):
        if self.high_scores and self.game_over:
            return self.high_scores[0].get('is_new', False)
        return False
    
    def get_stats_summary(self):
        """For end screen display."""
        return {
            'total_score': self.score,
            'category': self.category,
            'category_display': self.theme_manager.get_theme_display_name() if self.theme_manager else 'Capiz Cuisine',
            'multiplier': self.multiplier,
            'catches': self.catches_by_rarity.copy(),
            'best_catch': self.session_best_catch,
            'wish_status': self.get_wish_status()
        }