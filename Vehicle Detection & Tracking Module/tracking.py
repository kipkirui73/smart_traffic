# tracking.py

import math

class Tracker:
    def __init__(self):
        self.next_id = 0
        self.objects = {}  # id -> (x, y)

    def _get_center(self, box):
        x, y, w, h = box
        return (x + w // 2, y + h // 2)

    def _distance(self, c1, c2):
        return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

    def track_vehicles(self, boxes):
        """
        Assign IDs to detected boxes.
        Returns list of dicts:
        {id: int, box: (x, y, w, h)}
        """

        updated_objects = {}
        results = []

        for box in boxes:
            center = self._get_center(box)

            matched_id = None

            for obj_id, prev_center in self.objects.items():
                if self._distance(center, prev_center) < 50:
                    matched_id = obj_id
                    break

            if matched_id is None:
                matched_id = self.next_id
                self.next_id += 1

            updated_objects[matched_id] = center

            results.append({
                "id": matched_id,
                "box": box
            })

        self.objects = updated_objects
        return results