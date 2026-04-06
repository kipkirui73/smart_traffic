# modules/input/video_reader.py
# Developer 1 - Video Input & Preprocessing Module (Simple & Reliable)

import cv2
from config import VIDEO_PATH, FRAME_WIDTH, FRAME_HEIGHT

cap = None

def get_frame():
    global cap
    if cap is None:
        cap = cv2.VideoCapture(VIDEO_PATH)
        if not cap.isOpened():
            raise FileNotFoundError(f'Video not found: {VIDEO_PATH}')
    
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
