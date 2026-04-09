"""
src/cv/hand_tracker.py
Hand tracking module for GameFrick Project - CAFE OPTIMIZED.
Rey - CV Integration
"""

import cv2
import mediapipe as mp
import numpy as np
import sys
import os
import time
import warnings
from src.cv.camera_profile import CameraProfile

warnings.filterwarnings('ignore', category=UserWarning, module='mediapipe')


def _resolve_model_path(model_path):
    """
    Resolve the model path for both dev and PyInstaller .exe environments.
    When frozen, files are extracted to sys._MEIPASS at runtime.
    """
    if getattr(sys, 'frozen', False):
        # Running as .exe — look in PyInstaller's temp extraction folder
        base = sys._MEIPASS
    else:
        # Running as script — look relative to project root
        base = os.path.abspath('.')
    
    resolved = os.path.join(base, model_path)
    
    if not os.path.exists(resolved):
        raise FileNotFoundError(
            f"[HandTracker] hand_landmarker.task not found at: {resolved}\n"
            f"Make sure it is included in your PyInstaller spec datas."
        )
    
    return resolved


class HandTracker:
    """
    Single-hand tracker using MediaPipe 0.10.33 Task API.
    CAFE OPTIMIZED: Better low-light handling, velocity prediction for fast movement.
    
    OUTPUT FORMAT for Gio:
    - get_position() returns: (norm_x, norm_y) tuple
    - norm_x, norm_y: 0.0 to 1.0 (normalized screen coordinates)
    - Uses PALM CENTER for stability
    - Returns None if no hand detected (with prediction grace period)
    """
    
    def __init__(self, camera_index=0, model_path="hand_landmarker.task", 
                 camera_profile='front'):  # ADD camera_profile parameter
        
        self.camera_index = camera_index
        self.cap = None
        self.frame_timestamp = 0
        
        # NEW: Camera profile system
        self.profile = CameraProfile(camera_profile)
        print(f"[HandTracker] Using camera profile: {self.profile.get('name')}")
        
        # Smoothing buffer
        self.position_history = []
        self.missed_frames = 0
        self.max_missed = 3
        self.last_position = None
        self.velocity = (0, 0)
        self.max_prediction = 5
        self._last_landmarks = None

        # Resolve model path
        resolved_model_path = _resolve_model_path(model_path)
        print(f"[HandTracker] Loading model from: {resolved_model_path}")
        
        # MODIFIED: Use profile settings for MediaPipe
        mp_options = self.profile.get_mediapipe_options()
        
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
        from mediapipe.tasks.python.core.base_options import BaseOptions
        
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=resolved_model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=mp_options['min_hand_detection_confidence'],
            min_hand_presence_confidence=mp_options['min_hand_presence_confidence'],
            min_tracking_confidence=mp_options['min_tracking_confidence']
        )
        
        self.landmarker = HandLandmarker.create_from_options(options)
        
        print(f"[HandTracker] Profile '{camera_profile}' loaded")
        print(f"[HandTracker] Detection: {mp_options['min_detection_confidence']}, "
              f"Tracking: {mp_options['min_tracking_confidence']}")
    
    def start_camera(self):
        """Initialize camera capture with profile-specific settings."""
        # Try indices 0, 1, 2
        for index in [self.camera_index, 0, 1, 2]:
            self.cap = cv2.VideoCapture(index)
            if self.cap.isOpened():
                self.camera_index = index
                print(f"[HandTracker] Camera opened at index {index}")
                break
        
        if not self.cap.isOpened():
            raise RuntimeError("[HandTracker] No camera found on indices 0, 1, 2")
        
        # NEW: Apply profile-specific camera settings
        self.profile.apply_camera_settings(self.cap)
        
        # Set FPS
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"[HandTracker] Camera {self.camera_index} ready at {actual_fps:.0f}fps")
        return self
    
    def detect_hand(self, frame):
        """Process frame and return hand landmarks."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        from mediapipe.tasks.python.vision.core.image import Image, ImageFormat
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)
        
        self.frame_timestamp += 1
        detection_result = self.landmarker.detect_for_video(mp_image, self.frame_timestamp)
        
        if detection_result.hand_landmarks:
            self._last_landmarks = detection_result.hand_landmarks[0]
            return detection_result.hand_landmarks[0]
        return None
    
    def get_palm_center(self, hand_landmarks):
        """
        MODIFIED: Use profile-specific landmark selection.
        Returns position based on primary/backup landmark configuration.
        """
        if not hand_landmarks:
            return None
        
        # Get profile-specific landmark indices
        primary_indices, backup_indices = self.profile.get_landmark_indices()
        
        def get_average(indices):
            x_sum = sum(hand_landmarks[i].x for i in indices if i < len(hand_landmarks))
            y_sum = sum(hand_landmarks[i].y for i in indices if i < len(hand_landmarks))
            count = min(len(indices), len(hand_landmarks))
            if count == 0:
                return None
            return (x_sum / count, y_sum / count)
        
        # Try primary first
        pos = get_average(primary_indices)
        if pos is None:
            # Fallback to backup
            pos = get_average(backup_indices)
        
        return pos
    
    def smooth_position(self, new_pos):
        """Adaptive smoothing - less lag during fast movement."""
        if new_pos is None:
            return None
        
        self.position_history.append(new_pos)
        
        if len(self.position_history) >= 2:
            dx = abs(self.position_history[-1][0] - self.position_history[-2][0])
            dy = abs(self.position_history[-1][1] - self.position_history[-2][1])
            velocity = (dx + dy) / 2
            target_size = 3 if velocity > 0.05 else 5
        else:
            target_size = 5
        
        while len(self.position_history) > target_size:
            self.position_history.pop(0)
        
        avg_x = sum(p[0] for p in self.position_history) / len(self.position_history)
        avg_y = sum(p[1] for p in self.position_history) / len(self.position_history)
        return (avg_x, avg_y)
    
    def get_position(self, hand_landmarks):
        """
        Get smoothed position with VELOCITY PREDICTION for fast swipes.
        Returns: (norm_x, norm_y) or None
        """
        if hand_landmarks is None:
            self.missed_frames += 1
            
            if self.missed_frames <= self.max_prediction and self.last_position:
                speed = abs(self.velocity[0]) + abs(self.velocity[1])
                if speed > 0.08:
                    predicted_x = max(0.0, min(1.0, self.last_position[0] + self.velocity[0]))
                    predicted_y = max(0.0, min(1.0, self.last_position[1] + self.velocity[1]))
                    self.last_position = (predicted_x, predicted_y)
                    return self.last_position
            
            if self.missed_frames >= self.max_missed:
                self.position_history = []
                self.last_position = None
                self.velocity = (0, 0)
                return None
            
            return self.last_position
        
        self.missed_frames = 0
        raw_pos = self.get_palm_center(hand_landmarks)
        
        if self.last_position and raw_pos:
            self.velocity = (
                raw_pos[0] - self.last_position[0],
                raw_pos[1] - self.last_position[1]
            )
        
        smoothed = self.smooth_position(raw_pos)
        self.last_position = smoothed
        return smoothed
    
    def draw_skeleton(self, frame, hand_landmarks):
        """Draw hand skeleton with palm center highlighted."""
        if not hand_landmarks:
            return frame
        
        height, width, _ = frame.shape
        
        for landmark in hand_landmarks:
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
        
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (0, 5), (5, 9), (9, 13), (13, 17)
        ]
        
        for start_idx, end_idx in connections:
            if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                start = hand_landmarks[start_idx]
                end = hand_landmarks[end_idx]
                x1, y1 = int(start.x * width), int(start.y * height)
                x2, y2 = int(end.x * width), int(end.y * height)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        return frame
    
    def read_frame(self):
        """Grab a single frame."""
        if not self.cap:
            raise RuntimeError("[HandTracker] Camera not started. Call start_camera() first")
        success, frame = self.cap.read()
        return frame if success else None
    
    def stop(self):
        """Release resources."""
        if self.cap:
            self.cap.release()
        self.landmarker.close()
        cv2.destroyAllWindows()
        print("[HandTracker] Tracker stopped")