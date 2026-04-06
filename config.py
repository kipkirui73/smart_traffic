# config.py - Shared settings (everyone imports from here)

# ================== VIDEO INPUT SETTINGS (Developer 1) ==================
VIDEO_PATH = "data/traffic.mp4"
USE_CAMERA = False          # Change to True later for live camera
CAMERA_INDEX = 0            # 0 = default webcam

# Preprocessing settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
SKIP_FRAMES = 0             # Set to 2 or 3 to skip frames and run faster

# Color format
RETURN_RGB = False          # Set to True only if future YOLO needs RGB

# ================== SHARED SETTINGS (other developers) ==================
STOP_LINE_Y = 300
DB_PATH = "traffic.db"