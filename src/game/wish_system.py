"""
wish_system.py
Gacha prize mechanics for Capiztahan event.
Owner: Gio
Modified: Multiple wishes based on score thresholds (200, 400, 600, etc.)
"""

import random
import json
import os
from datetime import datetime

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


class WishSystem:
    THRESHOLD = 200           # Base threshold for first wish
    WIN_CHANCE = 0.40
    CODE_CHARS = 'ACDEFGHJKLMNPQRTUVWXYZ234679'
    CODE_LENGTH = 6
    LOG_FILE = "wishes_log.jsonl"
    VIDEO_NO_WISH = os.path.join("assets", "videos", "no_wish.mov")
    VIDEO_WISH_GRANTED = os.path.join("assets", "videos", "wish_granted.mov")

    def __init__(self, category='food'):
        self.category = category
        self._today_wins = 0

    def check_eligibility(self, score):
        return score >= self.THRESHOLD

    def get_progress(self, score):
        return min(1.0, score / self.THRESHOLD)

    def get_wish_status(self, score):
        """
        Returns how many wishes the player has earned and progress info.
        """
        total_wishes = score // self.THRESHOLD  # 200 = 1, 400 = 2, 600 = 3, etc.
        progress_to_next = (score % self.THRESHOLD) / self.THRESHOLD

        return {
            'total_earned': total_wishes,
            'current_score': score,
            'threshold': self.THRESHOLD,
            'progress_percent': progress_to_next * 100,
            'next_wish_at': (total_wishes + 1) * self.THRESHOLD,
            'eligible': total_wishes >= 1
        }

    def roll_wish(self, score, used_wishes=0):
        """
        Roll wishes based on score.
        score: player's current score
        used_wishes: how many wishes have already been used this game

        Returns result with all wishes rolled.
        """
        status = self.get_wish_status(score)
        total_wishes = status['total_earned']
        available_wishes = total_wishes - used_wishes

        if available_wishes <= 0:
            return {
                'eligible': False,
                'threshold': self.THRESHOLD,
                'current_score': score,
                'message': f'Reach {(total_wishes + 1) * self.THRESHOLD} points for another wish!',
                'can_retry': True,
                'video_paths': [],
                'auto_play': False,
                'wish_count': 0,
                'wishes': [],
                'codes': []
            }

        # Roll all available wishes
        wishes = []
        video_paths = []
        codes = []
        any_win = False

        for i in range(available_wishes):
            wish_num = used_wishes + i + 1
            won = random.random() < self.WIN_CHANCE

            if won:
                wish = self._generate_win(score, wish_num=wish_num, total_wishes=total_wishes)
                any_win = True
            else:
                wish = self._generate_loss(score, wish_num=wish_num, total_wishes=total_wishes)

            wishes.append(wish)
            video_paths.append(wish['video_path'])
            if wish.get('code'):
                codes.append(wish['code'])

        result = {
            'eligible': True,
            'won': any_win,  # True if ANY of the wishes won
            'wishes': wishes,
            'wish_count': len(wishes),
            'video_paths': video_paths,
            'codes': codes,
            'auto_play': True,
            'go_to_start': any_win,  # Go to start if any win
            'total_earned': total_wishes,
            'available_wishes': available_wishes
        }

        return result

    def _generate_win(self, score, wish_num=1, total_wishes=1):
        code = self._generate_code()

        result = {
            'eligible': True,
            'won': True,
            'code': code,
            'video_path': self.VIDEO_WISH_GRANTED,
            'wish_num': wish_num,
            'total_wishes': total_wishes,
            'message': f'\u2605 WISH GRANTED! Code: {code} \u2605'
        }

        self._log_result(score, result)
        return result

    def _generate_loss(self, score, wish_num=1, total_wishes=1):
        messages = [
            "Perla saw your effort! Try again!",
            "So close! Keep playing!",
            "The sea spirits weren't listening...",
            "Not this time, but don't give up!",
            "Your wish dissolved like sea foam..."
        ]

        result = {
            'eligible': True,
            'won': False,
            'video_path': self.VIDEO_NO_WISH,
            'wish_num': wish_num,
            'total_wishes': total_wishes,
            'message': random.choice(messages)
        }

        self._log_result(score, result)
        return result

    def _generate_code(self):
        return ''.join(random.choices(self.CODE_CHARS, k=self.CODE_LENGTH))

    def _log_result(self, score, result):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': self.category,
            'score': score,
            'threshold': self.THRESHOLD,
            'eligible': result['eligible'],
            'won': result.get('won', False),
            'code': result.get('code'),
            'wish_num': result.get('wish_num', 1),
            'total_wishes': result.get('total_wishes', 1),
            'session_id': self._generate_code()[:4]
        }

        try:
            with open(self.LOG_FILE, 'a') as f:
                if HAS_FCNTL:
                    fcntl.flock(f, fcntl.LOCK_EX)
                f.write(json.dumps(log_entry) + '\n')
                if HAS_FCNTL:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            print(f"[WishSystem] Failed to log result: {e}")


def make_wish(score, category='food', used_wishes=0):
    """
    Simple interface to roll wishes.

    Args:
        score: player's current score
        category: game category theme
        used_wishes: number of wishes already used this session

    Returns the full result dictionary with all available wishes.
    """
    system = WishSystem(category=category)
    return system.roll_wish(score, used_wishes=used_wishes)