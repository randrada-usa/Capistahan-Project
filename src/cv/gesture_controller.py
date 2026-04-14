"""
src/cv/gesture_controller.py
Bridge: Rey's HandTracker → Gio's GestureMapper → Jen's Player
Optimized to prevent double camera polling.
"""
import cv2
from src.cv.hand_tracker import HandTracker
from src.game.gesture_mapper import GestureMapper


class GestureController:
    """
    Unified interface for CV → Game communication.
    Handles camera lifecycle, hand tracking, and coordinate mapping.
    """
    
    def __init__(self, model_path="hand_landmarker.task", camera_profile='front'):
        # Pass camera_profile to HandTracker
        self.tracker = HandTracker(
            model_path=model_path,
            camera_profile=camera_profile
        )
        self.mapper = GestureMapper(
            smoothing=0.3,
            deadzone=0.02,
            loss_timeout=0.3
        )
        self.camera_started = False
        
        self.last_raw_frame = None
        self.last_debug_frame = None
        
        print(f"[GestureController] Initialized with profile: {camera_profile}")
    
    def start(self):
        self.tracker.start_camera()
        self.camera_started = True
        print("[GestureController] Camera started, tracker active")
        return self
    
    def stop(self):
        self.tracker.stop()
        self.camera_started = False
        print("[GestureController] Camera stopped")
    
    def update(self):
        """
        Single frame update. Reads camera ONCE and processes logic.
        Returns screen_x (int) or None if hand lost.
        """
        if not self.camera_started:
            return None
        
        # Read frame once
        frame = self.tracker.read_frame()
        if frame is None:
            self.last_debug_frame = None
            return None
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        self.last_raw_frame = frame.copy()
        
        # Detect hand once
        hand_landmarks = self.tracker.detect_hand(frame)
        
        # Build debug frame
        debug_frame = frame.copy()
        if hand_landmarks:
            debug_frame = self.tracker.draw_skeleton(debug_frame, hand_landmarks)
        
        # Get normalized position and map to screen x
        norm_pos = self.tracker.get_position(hand_landmarks)
        norm_x = norm_pos[0] if norm_pos else None
        result = self.mapper.map_x(norm_x)
        
        # Status overlay
        debug_info = self.mapper.get_debug_info()
        font = cv2.FONT_HERSHEY_SIMPLEX
        if debug_info['hand_present']:
            cv2.putText(debug_frame, "TRACKING", (20, 50),
                       font, 1.2, (0, 255, 0), 3)
        else:
            cv2.putText(debug_frame, "HAND LOST", (20, 50),
                       font, 1.2, (0, 0, 255), 3)
        
        self.last_debug_frame = debug_frame
        return result
    
    def get_debug_frame(self):
        """Returns the frame already processed in update()."""
        return self.last_debug_frame
    
    def reset(self):
        self.mapper.reset()
        self.last_debug_frame = None
        self.last_raw_frame = None
    
    def is_hand_present(self):
        return self.mapper.is_hand_present()