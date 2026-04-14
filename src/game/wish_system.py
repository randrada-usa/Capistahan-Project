"""
wish_system.py
Gacha prize mechanics for Capiztahan event.
Owner: Gio
"""

import random
import json
import os
from datetime import datetime

# Platform-specific file locking (Unix only, Windows skips)
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


class WishSystem:
    """
    Handles post-game wish mechanics:
    - Eligibility check (score threshold)
    - Probability roll (20% win rate)
    - Verification code generation
    - Prize logging for analytics
    """
    
    # Score needed to unlock wish
    THRESHOLD = 200
    
    # Win probability (0.0 to 1.0)
    WIN_CHANCE = 0.70
    
    # Code generation alphabet (no ambiguous chars: O/0, I/l)
    CODE_CHARS = 'ACDEFGHJKLMNPQRTUVWXYZ234679'
    CODE_LENGTH = 6
    
    # Log file for analytics
    LOG_FILE = "wishes_log.jsonl"
    
    def __init__(self, category='food'):
        self.category = category
        self._today_wins = 0
    
    def check_eligibility(self, score):
        """Returns True if score meets threshold."""
        return score >= self.THRESHOLD
    
    def get_progress(self, score):
        """Returns 0.0 to 1.0 progress toward threshold."""
        return min(1.0, score / self.THRESHOLD)
    
    def roll_wish(self, score):
        """
        Main entry point. Returns complete result dict.
        Call this from end_screen.py when player clicks "Make Wish"
        """
        # Not eligible
        if not self.check_eligibility(score):
            return {
                'eligible': False,
                'threshold': self.THRESHOLD,
                'current_score': score,
                'message': f'Reach {self.THRESHOLD} points to make a wish!',
                'can_retry': True
            }
        
        # Roll the dice
        won = random.random() < self.WIN_CHANCE
        
        if won:
            return self._generate_win(score)
        else:
            return self._generate_loss(score)
    
    def _generate_win(self, score):
        """Create win result with code and logging."""
        code = self._generate_code()
        
        result = {
            'eligible': True,
            'won': True,
            'code': code,
            'verification_code': code,
            'instructions': 'Show this code to the 6-byte Studios booth staff.',
            'booth_location': 'Capiztahan Main Stage'
        }
        
        self._log_result(score, result)
        return result
    
    def _generate_loss(self, score):
        """Create loss result with encouragement."""
        result = {
            'eligible': True,
            'won': False,
            'code': None,
            'prize_tier': None,
            'message': random.choice([
                'So close! The spirits of Capiz were not aligned.',
                'Not this time, but your offering was noted!',
                'The gacha gods smile upon your next attempt.',
                'Better luck in the next round of Capiztahan!',
                'The bay waters were calm, but not favorable today.'
            ]),
            'can_retry': True,
            'hint': 'Try for rarer items to boost your score!',
            'encouragement': 'You can play again and make another wish!'
        }
        
        self._log_result(score, result)
        return result
    
    def _generate_code(self):
        """Generate unique verification code."""
        return ''.join(random.choices(self.CODE_CHARS, k=self.CODE_LENGTH))
    
    def _select_prize_tier(self):
        """Weighted selection from active prize tiers."""
        active_tiers = {
            k: v for k, v in self.PRIZE_TIERS.items() 
            if v['weight'] > 0
        }
        
        if not active_tiers:
            return 'rare'
        
        tiers = list(active_tiers.keys())
        weights = [active_tiers[t]['weight'] for t in tiers]
        
        return random.choices(tiers, weights=weights, k=1)[0]
    
    def _log_result(self, score, result):
        """Append result to analytics log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': self.category,
            'score': score,
            'threshold': self.THRESHOLD,
            'eligible': result['eligible'],
            'won': result.get('won', False),
            'code': result.get('code'),
            'prize_tier': result.get('prize_tier'),
            'session_id': self._generate_code()[:4]
        }
        
        try:
            # Simple append mode (safe for single-player game)
            # File locking only applied on Unix systems
            with open(self.LOG_FILE, 'a') as f:
                if HAS_FCNTL:
                    fcntl.flock(f, fcntl.LOCK_EX)
                
                f.write(json.dumps(log_entry) + '\n')
                
                if HAS_FCNTL:
                    fcntl.fcntl.flock(f, fcntl.LOCK_UN)
                    
        except Exception as e:
            print(f"[WishSystem] Log error: {e}")
    
    def get_analytics_summary(self):
        """
        Return stats for 6-byte Studios dashboard.
        Call this on game startup to show 'X winners today!'
        """
        if not os.path.exists(self.LOG_FILE):
            return {
                'total_attempts': 0, 
                'total_wins': 0, 
                'win_rate': 0,
                'today_wins': 0
            }
        
        total = 0
        wins = 0
        today = datetime.now().date().isoformat()
        today_wins = 0
        
        try:
            with open(self.LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        total += 1
                        if entry.get('won'):
                            wins += 1
                            if entry['timestamp'].startswith(today):
                                today_wins += 1
                    except json.JSONDecodeError:
                        continue  # Skip corrupted lines
        except Exception as e:
            print(f"[WishSystem] Analytics error: {e}")
        
        return {
            'total_attempts': total,
            'total_wins': wins,
            'win_rate': wins / total if total > 0 else 0,
            'today_wins': today_wins,
            'target_win_rate': self.WIN_CHANCE
        }


# Convenience function for simple integration
def make_wish(score, category='food'):
    """
    One-shot function for end_screen.py
    Returns result dict directly.
    """
    wish = WishSystem(category=category)
    return wish.roll_wish(score)