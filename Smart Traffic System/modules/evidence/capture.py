# modules/evidence/capture.py
import cv2
import time
import os

os.makedirs("evidence", exist_ok=True)

def save_evidence(frame, vehicle_id):
    """Save image evidence when violation occurs"""
    if frame is None:
        return None
    
    timestamp = int(time.time())
    filename = f"evidence/vehicle_{vehicle_id}_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    return filename