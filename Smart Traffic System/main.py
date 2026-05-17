# main.py
from modules.input.video_reader import get_frame, preprocess_frame
from modules.detection.detect import detect_vehicles
from modules.tracking.tracker import track_vehicles
from modules.violations.violation import check_violation
from modules.evidence.capture import save_evidence
from modules.plate_reader.reader import read_plate
from database.db import init_db, log_violation
import cv2
import logging

init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 Real Scalable Smart Traffic System Starting...")

while True:
    raw_frame = get_frame()
    if raw_frame is None:
        logger.info("Video ended.")
        break
    
    frame = preprocess_frame(raw_frame)
    
    # Detection + Tracking
    detections = detect_vehicles(frame)
    tracked = track_vehicles(detections)
    
    # Violation Check + Evidence + Plate Reading
    for vehicle in tracked:
        if check_violation(vehicle):
            plate = read_plate(frame, vehicle["box"])
            path = save_evidence(frame, vehicle["id"])
            log_violation(
                vehicle_id=vehicle["id"],
                image_path=path,
                confidence=vehicle.get("confidence", 0.0),
                plate_number=plate
            )
            plate_display = plate if plate else "unknown"
            logger.warning(
                f"VIOLATION DETECTED - Vehicle {vehicle['id']} | Plate: {plate_display}"
            )
    
    # Visualization
    for vehicle in tracked:
        x, y, w, h = vehicle["box"]
        is_violation = check_violation(vehicle)
        color = (0, 0, 255) if is_violation else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # Show plate text on the video feed if available
        plate = vehicle.get("plate")
        label = f"ID:{vehicle['id']}  {vehicle.get('confidence',0):.2f}"
        if plate:
            label += f"  [{plate}]"
        cv2.putText(frame, label,
                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    cv2.imshow("Smart Traffic System", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
logger.info("System stopped. Run dashboard/app.py separately to view records.")