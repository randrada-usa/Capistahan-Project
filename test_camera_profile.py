# test_camera_profile.py
# Save this in your project root folder, then run: python test_camera_profile.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cv.camera_profile import CameraProfile

print("=" * 50)
print("CAMERA PROFILE TEST")
print("=" * 50)

# Test front profile
print("\n--- FRONT PROFILE ---")
front = CameraProfile('front')
print(f"Name: {front.get('name')}")
print(f"Detection confidence: {front.get('min_detection_confidence')}")
print(f"Primary landmark: {front.get('primary_landmark')}")
print(f"Auto exposure: {front.get('auto_exposure')}")

# Test high_angle profile  
print("\n--- HIGH-ANGLE PROFILE ---")
high = CameraProfile('high_angle')
print(f"Name: {high.get('name')}")
print(f"Detection confidence: {high.get('min_detection_confidence')}")
print(f"Primary landmark: {high.get('primary_landmark')}")
print(f"Manual exposure: {high.get('manual_exposure')}")
print(f"Brightness: {high.get('brightness')}")

# Test invalid (should fallback to front)
print("\n--- INVALID PROFILE (FALLBACK) ---")
invalid = CameraProfile('invalid')
print(f"Fallback name: {invalid.get('name')}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)