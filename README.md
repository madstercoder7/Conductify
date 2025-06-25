# Conductify - Gesture-Based Music Controller

Control your music with hand gestures using OpenCV and MediaPipe.

## Load music
- Use mp3 files which you already have avaialable
- Use this website https://spotdownloader.com/ to download your playlists from your spotify account 

## Features
| Gesture          | Action               |
|------------------|----------------------|
| 🖐️ Open Palm     | Play Music           |
| ✊ Fist           | Pause Music          |
| 🤏 Pinch + Drag  | Adjust Volume        |
| 👉👈 Swipe (Index Finger) | Next / Previous Track |

## Installation

1. **Clone this repository**
```bash
git clone https://github.com/madstercoder7/Conductify.git
cd conductify
```

2. **Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the app**
```bash
python app.py
```

## Improvements coming soon
- Better gesture recognition using custom gesture models
- Other music player features 
- Multi platform Compatibility
- Spotify integration for premium users
- Custom gestures users can design as per their convenience