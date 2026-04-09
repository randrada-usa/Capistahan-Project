# GameFrick Project - Gesture Cafe Game

OpenCV + MediaPipe hand-tracking game for cafe pop-ups. Student project by GameFrick team.

## 🎯 Quick Overview

We're building a gesture-controlled game where players use hand/body movements to interact with the screen — no touching required! Perfect for cafes and pop-up events.

## 👥 Team

| Name | Role | What I Do |
|------|------|-----------|
| Rey | Team Lead / CV Integration | Hand tracking, gesture recognition, architecture |
| Gio | Gesture Detection / Game Logic | What counts as a "swipe", scoring system |
| Jen | UI / Game States | Screens, buttons, menus, visual feedback |
| Ele | Sound Engineer | Sound effects, background music, audio polish |
| Tris | Marketing / Cafe Outreach | Selling to shops, demos, feedback collection |

## 🛠️ Tech Stack

- **Python 3.11** (programming language)
- **OpenCV** (computer vision, camera access)
- **MediaPipe** (hand tracking, gesture detection)
- **Pygame** (game graphics, sounds, input)
- **NumPy** (math and arrays)

## 📁 Project Structure
GameFrick-Project/
├── venv/                 # Virtual environment (Python packages)
├── main.py                    # Entry point - wires everything
├── src/
│   ├── cv/
│   │   ├── __init__.py
│   │   ├── hand_tracker.py    # Rey's code
│   │   └── gesture_controller.py  # Bridge (from earlier)
│   ├── game/
│   │   ├── __init__.py
│   │   ├── player.py          # Updated with sprite + freeze
│   │   ├── gesture_mapper.py  # Gio's code
│   │   ├── falling_objects.py # Updated with sprites
│   │   ├── game_state.py      # Score, lives, game over
│   │   └── asset_manager.py   # NEW - loads and scales sprites
│   └── ui/
│       └── screens.py         # Phase 3 - for now simple HUD
└── assets/
    ├── backgrounds/background.png
    └── sprites/
        ├── Sprite (default).png
        ├── Good item.png
        └── Bad item.png
├── tools/               # Helper scripts
├── docs/                # Notes, meeting minutes
├── .gitignore
├── requirements.txt
└── README.md
plain
Copy

## 🚀 Setup Guide for Beginners

### Step 1: Install Python 3.11

1. Go to https://www.python.org/downloads/release/python-3119/
2. Download: **Windows installer (64-bit)** `python-3.11.9-amd64.exe`
3. Run installer, ☑️ **CHECK "Add Python to PATH"**
4. Click **Install Now**
5. If asked about long paths, click **Yes**
6. **Restart your computer**

### Step 2: Get the Code from GitHub

Using GitHub Desktop or PowerShell:
```powershell
cd Documents
git clone https://github.com/YOUR_USERNAME/GameFrick-Project.git
cd GameFrick-Project
Step 3: Create Virtual Environment
powershell
Copy
py -3.11 -m venv venv
Step 4: Activate Virtual Environment
powershell
Copy
venv\Scripts\activate
Success check: Prompt shows (venv) at start.
Step 5: Install Required Packages
powershell
Copy
pip install -r requirements.txt
Step 6: Test Everything Works
powershell
Copy
python tools\test_setup.py
Expected:
plain
Copy
result:
opencv-python==4.11.0.86
mediapipe==0.10.33
pygame==2.6.1
numpy==1.26.4

🎉 All systems ready for dev day!
🔄 Daily Workflow
powershell
Copy
# 1. Go to project
cd Documents\GitHub\GameFrick-Project

# 2. Activate environment
venv\Scripts\activate

# 3. Get latest changes
git pull origin main

# 4. Work on code...

# 5. Save changes
git add .
git commit -m "What I did"
git push origin main

# 6. Done
deactivate
🆘 Troubleshooting
Table
Problem	Solution
"Python was not found"	Reinstall Python 3.11, check "Add to PATH"
"'venv' is not recognized"	Use py -3.11 not python
"Permission denied"	Run Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
"No module named 'cv2'"	Run venv\Scripts\activate first
Git "not a git repository"	Make sure you're in GameFrick-Project folder

📝 First Code Test
Create test_camera.py:
Python
Copy
import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.imshow('Camera Test - Press Q to quit', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

Run: python test_camera.py
You should see your webcam! Press Q to close.