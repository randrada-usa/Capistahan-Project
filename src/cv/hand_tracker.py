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
    
    def __init__(self, camera_index=0, model_path="hand_landmarker.task"):
        self.camera_index = camera_index
        self.cap = None
        self.frame_timestamp = 0
        
        # Smoothing buffer
        self.position_history = []
        
        # Grace period and prediction
        self.missed_frames = 0
        self.max_missed = 3
        self.last_position = None
        self.velocity = (0, 0)
        self.max_prediction = 5
        self._last_landmarks = None

        # Resolve model path for both dev and .exe
        resolved_model_path = _resolve_model_path(model_path)
        print(f"[HandTracker] Loading model from: {resolved_model_path}")
        
        # MediaPipe - LOWERED THRESHOLDS for cafe lighting
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
        from mediapipe.tasks.python.core.base_options import BaseOptions
        
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=resolved_model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.3,
            min_hand_presence_confidence=0.3,
            min_tracking_confidence=0.3
        )
        
        self.landmarker = HandLandmarker.create_from_options(options)
        
        print("[HandTracker] MediaPipe HandLandmarker loaded (CAFE MODE)")
        print("[HandTracker] Settings: detection=0.3, palm center, velocity prediction, auto-exposure")
    
    def start_camera(self):
        """Initialize camera capture - tries multiple indices for reliability."""
        # Try indices 0, 1, 2 in case default camera index fails in .exe
        for index in [self.camera_index, 0, 1, 2]:
            self.cap = cv2.VideoCapture(index)
            if self.cap.isOpened():
                self.camera_index = index
                print(f"[HandTracker] Camera opened at index {index}")
                break
        
        if not self.cap.isOpened():
            raise RuntimeError("[HandTracker] No camera found on indices 0, 1, 2")
        
        # Cafe lighting: Auto-exposure with gain boost
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_GAIN, 200)
        
        # Fallback if auto not supported
        if self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE) < 0:
            print("[HandTracker] Auto-exposure not supported, switching to manual bright mode")
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -4)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
        
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"[HandTracker] Camera {self.camera_index} started ({actual_fps:.0f}fps, cafe lighting mode)")
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
        """Calculate palm center from wrist + finger bases."""
        if not hand_landmarks:
            return None
        
        indices = [0, 5, 9, 13, 17]
        x_sum = sum(hand_landmarks[i].x for i in indices)
        y_sum = sum(hand_landmarks[i].y for i in indices)
        return (x_sum / 5, y_sum / 5)
    
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