"""
Gesture Mapper Module
Converts normalized hand X coordinate to game screen X coordinate.
Handles smoothing, deadzone, and edge clamping.

Owner: Gio
Input: Rey's HandController.get_hand_x() → float 0.0-1.0 or None
Output: Jen's Player position (screen_x: int or None)
"""

import time


class GestureMapper:
    """
    Maps normalized hand X (0.0-1.0) to screen X with smoothing and edge clamping.
    Y-axis is fixed at 980 per Jen's spec.
    """
    
    def __init__(self, 
                 smoothing=0.3,      # EMA alpha: higher = more responsive
                 deadzone=0.02,       # Min movement to register (normalized)
                 loss_timeout=0.3):   # Seconds before declaring hand lost
        
        # Jen's specs
        self.screen_w = 1920
        self.screen_h = 1080
        self.player_y = 955  # Fixed per Jen
        
        # Tuning params
        self.alpha = smoothing
        self.deadzone = deadzone
        self.loss_timeout = loss_timeout
        
        # State
        self.smoothed_norm_x = 0.5
        self.last_hand_time = None
        self.hand_present = False
        self._last_raw_x = 0.5  # For debug
        
    def map_x(self, norm_x):
        """
        Convert Rey's normalized hand X to screen X coordinate.
        
        Args:
            norm_x: float 0.0-1.0 from HandController, or None if no hand
        
        Returns:
            screen_x (int 0-1920) or None if hand lost
        """
        # Hand loss handling — return None, Jen freezes player
        if norm_x is None:
            if self.last_hand_time and (time.time() - self.last_hand_time > self.loss_timeout):
                self.hand_present = False
            return None
        
        # Safety clamp
        norm_x = max(0.0, min(1.0, norm_x))
        self._last_raw_x = norm_x
        
        # Update state
        self.last_hand_time = time.time()
        self.hand_present = True
        
        # Smoothing with deadzone
        delta = abs(norm_x - self.smoothed_norm_x)
        if delta > self.deadzone:
            self.smoothed_norm_x = (self.alpha * norm_x + 
                                   (1 - self.alpha) * self.smoothed_norm_x)
        
        # Convert to screen coordinates
        screen_x = int(self.smoothed_norm_x * self.screen_w)
        return max(0, min(self.screen_w, screen_x))
        
    def get_player_y(self):
        """Return fixed Y position (980)."""
        return self.player_y
        
    def is_hand_present(self):
        """Check if hand tracked within timeout window."""
        return self.hand_present
        
    def reset(self):
        """Reset to center. Call on game restart."""
        self.smoothed_norm_x = 0.5
        self.hand_present = False
        self.last_hand_time = None
        
    def tune(self, smoothing=None, deadzone=None):
        """Runtime parameter adjustment."""
        if smoothing is not None:
            self.alpha = max(0.0, min(1.0, smoothing))
        if deadzone is not None:
            self.deadzone = max(0.0, min(0.5, deadzone))
            
    def get_debug_info(self):
        """Debug data for Rey's overlay or Jen's HUD."""
        return {
            'hand_present': self.hand_present,
            'raw_norm_x': self._last_raw_x,
            'smoothed_norm_x': self.smoothed_norm_x,
            'screen_x': int(self.smoothed_norm_x * self.screen_w) if self.hand_present else None,
            'player_y': self.player_y
        }