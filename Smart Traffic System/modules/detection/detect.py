# modules/detection/detect.py
from ultralytics import YOLO
import logging

# Load the model once (global)
model = YOLO("yolov8n.pt")   # Start with nano (fast). Later try yolov8s.pt or yolov8m.pt

# Vehicle classes in COCO dataset (YOLOv8)
VEHICLE_CLASSES = [2, 3, 5, 7]   # car, motorcycle, bus, truck

def detect_vehicles(frame):
    """
    Real YOLOv8 vehicle detection.
    Returns list of (x, y, w, h, confidence)
    """
    if frame is None:
        return []
    
    # Run inference
    results = model(frame, conf=0.4, iou=0.45, classes=VEHICLE_CLASSES, verbose=False)[0]
    
    detections = []
    
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()   # bounding box coordinates
        conf = float(box.conf[0])                # confidence score
        x = int(x1)
        y = int(y1)
        w = int(x2 - x1)
        h = int(y2 - y1)
        
        detections.append((x, y, w, h, conf))
    
    return detections

    
"""# modules/detection/detect.py
import random
import logging

# Placeholder for real YOLO
# from ultralytics import YOLO
# model = YOLO("yolov8n.pt")   # Uncomment when you have the model

def detect_vehicles(frame):
    
    Mock detection now. 
    Replace this function with real YOLO when ready.
    Returns list of (x, y, w, h, confidence)

    if frame is None:
        return []
    
    h, w, _ = frame.shape
    detections = []
    
    # Mock with confidence scores
    num_vehicles = random.randint(1, 5)
    for _ in range(num_vehicles):
        x = random.randint(0, w - 100)
        y = random.randint(0, h - 100)
        conf = round(random.uniform(0.6, 0.95), 2)
        detections.append((x, y, 80, 50, conf))
    
    return detections   # Later: return model(frame)[0].boxes.data """


# modules/detection/detect.py
from ultralytics import YOLO
import logging

# Load the model once (global)
model = YOLO("yolov8n.pt")   # Start with nano (fast). Later try yolov8s.pt or yolov8m.pt

# Vehicle classes in COCO dataset (YOLOv8)
VEHICLE_CLASSES = [2, 3, 5, 7]   # car, motorcycle, bus, truck

def detect_vehicles(frame):
    """
    Real YOLOv8 vehicle detection.
    Returns list of (x, y, w, h, confidence)
    """
    if frame is None:
        return []
    
    # Run inference
    results = model(frame, conf=0.4, iou=0.45, classes=VEHICLE_CLASSES, verbose=False)[0]
    
    detections = []
    
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()   # bounding box coordinates
        conf = float(box.conf[0])                # confidence score
        x = int(x1)
        y = int(y1)
        w = int(x2 - x1)
        h = int(y2 - y1)
        
        detections.append((x, y, w, h, conf))
    
    return detections