# detection.py

import random

def detect_vehicles(frame):
    """
    Simulates vehicle detection.
    Returns a list of bounding boxes: (x, y, w, h)
    """

    height, width, _ = frame.shape

    boxes = []

    # simulate 2–5 vehicles
    num_vehicles = random.randint(2, 5)

    for _ in range(num_vehicles):
        x = random.randint(0, width - 100)
        y = random.randint(0, height - 100)
        w = random.randint(40, 100)
        h = random.randint(40, 100)

        boxes.append((x, y, w, h))

    return boxes