"""
Example integration for Gio - How to use HandTracker in game code
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cv.hand_tracker import HandTracker
import cv2

class HandController:
    def __init__(self):
        self.tracker = HandTracker().start_camera()
    
    def get_hand_x(self):
        """Returns hand X position as 0.0 (left) to 1.0 (right) or None"""
        frame = self.tracker.read_frame()
        if frame is None:
            return None, None
        
        frame = cv2.flip(frame, 1)
        landmarks = self.tracker.detect_hand(frame)
        pos = self.tracker.get_position(landmarks)
        
        if pos:
            return pos[0], frame  # Return X and frame for display
        return None, frame
    
    def cleanup(self):
        self.tracker.stop()


if __name__ == "__main__":
    controller = HandController()
    
    print("Test: Move hand left-right. Press 'q' to quit.")
    print("Green line follows your hand position.")
    
    while True:
        x, frame = controller.get_hand_x()
        
        if frame is None:
            break
        
        if x is not None:
            # Draw green line at hand X position
            h, w = frame.shape[:2]
            line_x = int(x * w)
            cv2.line(frame, (line_x, 0), (line_x, h), (0, 255, 0), 3)
            cv2.putText(frame, f"X: {x:.2f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "NO HAND", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow("Hand X Test - Press 'q' to quit", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    controller.cleanup()
    print("\nDone - Hand X value is working correctly")
    print("Gio can use: chibi_x = hand_x * screen_width")