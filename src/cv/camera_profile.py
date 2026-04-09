"""
camera_profile.py
Camera calibration profiles for different mounting positions.
Rey - CV Architecture Module
"""

import cv2


class CameraProfile:
    """
    Configuration for hand tracking based on camera mounting position.
    """
    
    PROFILES = {
        'front': {
            'name': 'Front-facing Webcam',
            'description': 'Standard laptop webcam at eye level',
            
            # MediaPipe detection thresholds (full key names)
            'min_hand_detection_confidence': 0.3,
            'min_hand_presence_confidence': 0.3,
            'min_tracking_confidence': 0.3,
            
            # Landmark selection
            'primary_landmark': 'palm_center',
            'backup_landmark': 'wrist',
            
            # Camera settings
            'auto_exposure': 0.75,
            'manual_exposure': None,
            'brightness': None,
            'contrast': None,
            
            # Position mapping
            'flip_horizontal': True,
            'y_axis_enabled': False,
        },
        
        'high_angle': {
            'name': 'High-Angle Overhead',
            'description': 'Camera mounted above monitor, pointing down 45-60°',
            
            # Lower thresholds for smaller/distant hand (full key names)
            'min_hand_detection_confidence': 0.25,
            'min_hand_presence_confidence': 0.25,
            'min_tracking_confidence': 0.25,
            
            # Different landmark priority for top-down view
            'primary_landmark': 'wrist',
            'backup_landmark': 'middle_finger_base',
            
            # Camera settings for overhead lighting
            'auto_exposure': 0.25,
            'manual_exposure': -4,
            'brightness': 150,
            'contrast': 128,
            
            # Same position mapping
            'flip_horizontal': True,
            'y_axis_enabled': False,
        }
    }
    
    def __init__(self, profile_name='front'):
        self._profile = self.PROFILES.get(profile_name, self.PROFILES['front'])
        self._name = profile_name
        
        if profile_name not in self.PROFILES:
            print(f"[CameraProfile] Unknown profile '{profile_name}', using 'front'")
    
    def get(self, key, default=None):
        """Get configuration value."""
        return self._profile.get(key, default)
    
    def apply_camera_settings(self, cap):
        """
        Apply OpenCV camera settings based on profile.
        """
        auto_exp = self.get('auto_exposure')
        if auto_exp is not None:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exp)
        
        manual_exp = self.get('manual_exposure')
        if manual_exp is not None and auto_exp == 0.25:
            cap.set(cv2.CAP_PROP_EXPOSURE, manual_exp)
        
        brightness = self.get('brightness')
        if brightness is not None:
            cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        
        contrast = self.get('contrast')
        if contrast is not None:
            cap.set(cv2.CAP_PROP_CONTRAST, contrast)
        
        print(f"[CameraProfile] Applied '{self._name}' settings to camera")
    
    def get_landmark_indices(self):
        """
        Return MediaPipe landmark indices for primary and backup points.
        """
        primary_name = self.get('primary_landmark')
        backup_name = self.get('backup_landmark')
        
        landmark_map = {
            'wrist': [0],
            'palm_center': [0, 5, 9, 13, 17],
            'middle_finger_base': [9],
            'index_finger_base': [5],
        }
        
        primary = landmark_map.get(primary_name, [0])
        backup = landmark_map.get(backup_name, [0])
        
        return primary, backup
    
    def get_mediapipe_options(self):
        """
        Return MediaPipe HandLandmarker options dict with CORRECT key names.
        """
        return {
            'min_hand_detection_confidence': self.get('min_hand_detection_confidence'),
            'min_hand_presence_confidence': self.get('min_hand_presence_confidence'),
            'min_tracking_confidence': self.get('min_tracking_confidence'),
        }
    
    @classmethod
    def list_profiles(cls):
        """Return available profile names."""
        return list(cls.PROFILES.keys())
    
    @classmethod
    def get_profile_info(cls, name):
        """Get human-readable info about a profile."""
        p = cls.PROFILES.get(name)
        if p:
            return f"{p['name']}: {p['description']}"
        return "Unknown profile"