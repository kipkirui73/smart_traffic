# modules/violations/violation.py
from config import STOP_LINE_Y

def check_violation(vehicle):
    if not vehicle or "box" not in vehicle:
        return False
    x, y, w, h = vehicle["box"]
    center_y = y + h // 2
    return center_y > STOP_LINE_Y