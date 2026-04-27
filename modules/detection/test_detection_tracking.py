# test_detection_tracking.py

import cv2
from detection import detect_vehicles
from tracking import Tracker

tracker = Tracker()

# use webcam (or replace with video file later)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    boxes = detect_vehicles(frame)
    tracked = tracker.track_vehicles(boxes)

    for obj in tracked:
        x, y, w, h = obj["box"]
        obj_id = obj["id"]

        # draw box
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # draw ID
        cv2.putText(frame, f"ID {obj_id}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Detection & Tracking", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()