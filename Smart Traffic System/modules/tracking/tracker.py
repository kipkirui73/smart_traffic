# modules/tracking/tracker.py
vehicle_id_counter = 0

def track_vehicles(detections):
    """
    detections = list of (x, y, w, h, conf)
    Returns list of dicts
    """
    global vehicle_id_counter
    tracked = []
    
    for det in detections:
        x, y, w, h, conf = det
        vehicle_id_counter += 1
        tracked.append({
            "id": vehicle_id_counter,
            "box": (x, y, w, h),
            "confidence": conf
        })
    return tracked