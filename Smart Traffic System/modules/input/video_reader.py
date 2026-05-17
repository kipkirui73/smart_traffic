# modules/input/video_reader.py
# Developer 1 - Video Input & Preprocessing Module (Simple & Reliable)

import cv2
import os
from config import VIDEO_PATH, FRAME_WIDTH, FRAME_HEIGHT, USE_CAMERA, CAMERA_INDEX

cap = None

def get_frame():
    global cap
    if cap is None:
        if USE_CAMERA:
            cap = cv2.VideoCapture(CAMERA_INDEX)
        else:
            if not os.path.exists(VIDEO_PATH):
                raise FileNotFoundError(
                    f'Video not found: {VIDEO_PATH}\n'
                    'Place traffic.mp4 in Smart Traffic System/data or set USE_CAMERA=True in config.py.'
                )
            cap = cv2.VideoCapture(VIDEO_PATH)

        if not cap.isOpened():
            cap = None
            source = f'camera index {CAMERA_INDEX}' if USE_CAMERA else VIDEO_PATH
            raise FileNotFoundError(f'Unable to open video source: {source}')
    
    ret, frame = cap.read()
    if not ret:
        cap.release()
        cap = None
        return None
    return frame

def preprocess_frame(frame):
    if frame is None:
        return None
    resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    return resized
