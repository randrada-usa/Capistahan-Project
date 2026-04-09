"""
Test script for dev day - verify all imports work
Run this: python tools/test_setup.py
"""

import sys

def test_imports():
    """Check all required libraries are installed"""
    errors = []
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        errors.append(f"❌ OpenCV: {e}")
    
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe: {mp.__version__}")
    except ImportError as e:
        errors.append(f"❌ MediaPipe: {e}")
    
    try:
        import pygame
        print(f"✅ Pygame: {pygame.version.ver}")
    except ImportError as e:
        errors.append(f"❌ Pygame: {e}")
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        errors.append(f"❌ NumPy: {e}")
    
    if errors:
        print("\n--- ERRORS ---")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\n All systems ready for dev day!")

if __name__ == "__main__":
    test_imports()
