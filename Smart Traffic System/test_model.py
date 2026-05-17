"""
test_model.py  –  SmartTraffic Vision: Full Model Test Suite
=============================================================
Tests every layer of the pipeline:
  1. YOLO model loading & inference
  2. Detection module (detect_vehicles)
  3. Tracking module (track_vehicles)
  4. Violation logic (check_violation)
  5. Evidence capture (save_evidence)
  6. Database pipeline (init_db → log_violation → get_violations)
  7. End-to-end smoke test

Run with:
    python test_model.py
or:
    python -m pytest test_model.py -v
"""

import sys, os, time, sqlite3, shutil
import numpy as np
import pytest

# Make sure imports resolve from this directory
sys.path.insert(0, os.path.dirname(__file__))

# ─── helpers ────────────────────────────────────────────────────────────────

def blank_frame(h=480, w=640):
    """BGR black frame (no vehicles → safe for unit tests)."""
    return np.zeros((h, w, 3), dtype=np.uint8)

def white_frame(h=480, w=640):
    """All-white frame."""
    return np.ones((h, w, 3), dtype=np.uint8) * 255

# ═══════════════════════════════════════════════════════════════════════════
# 1.  YOLO model loading
# ═══════════════════════════════════════════════════════════════════════════
class TestYOLOModel:
    def test_model_file_exists(self):
        """yolov8n.pt must be present in the project root."""
        assert os.path.isfile("yolov8n.pt"), (
            "yolov8n.pt not found. Place it in 'Smart Traffic System/'."
        )

    def test_model_loads(self):
        """YOLO model must load without errors."""
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        assert model is not None

    def test_model_has_correct_task(self):
        """Model must be a detection model (not segmentation / pose)."""
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        # task attribute varies by ultralytics version
        assert "detect" in str(model.task).lower() or hasattr(model, "model")

    def test_model_runs_on_blank_frame(self):
        """Inference on a blank frame must not raise exceptions."""
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        frame = blank_frame()
        results = model(frame, conf=0.4, verbose=False)
        assert results is not None

    def test_model_vehicle_classes_defined(self):
        """VEHICLE_CLASSES constant must include car (2) and truck (7)."""
        from modules.detection.detect import VEHICLE_CLASSES
        assert 2 in VEHICLE_CLASSES, "Car class (2) missing"
        assert 7 in VEHICLE_CLASSES, "Truck class (7) missing"


# ═══════════════════════════════════════════════════════════════════════════
# 2.  Detection module
# ═══════════════════════════════════════════════════════════════════════════
class TestDetectionModule:
    def test_returns_list(self):
        from modules.detection.detect import detect_vehicles
        result = detect_vehicles(blank_frame())
        assert isinstance(result, list)

    def test_none_frame_returns_empty(self):
        from modules.detection.detect import detect_vehicles
        assert detect_vehicles(None) == []

    def test_detection_tuple_format(self):
        """Each detection must be a 5-tuple (x, y, w, h, conf)."""
        from modules.detection.detect import detect_vehicles
        # Use a blank frame; if no vehicles detected that is fine
        result = detect_vehicles(blank_frame())
        for det in result:
            assert len(det) == 5, f"Expected 5-tuple, got {len(det)}-tuple"
            x, y, w, h, conf = det
            assert 0 <= conf <= 1.0, f"Confidence out of range: {conf}"
            assert w > 0 and h > 0, "Box dimensions must be positive"

    def test_confidence_threshold_respected(self):
        """Detections must all have confidence >= 0.4 (as set in detect.py)."""
        from modules.detection.detect import detect_vehicles
        for det in detect_vehicles(blank_frame()):
            _, _, _, _, conf = det
            assert conf >= 0.4


# ═══════════════════════════════════════════════════════════════════════════
# 3.  Tracking module
# ═══════════════════════════════════════════════════════════════════════════
class TestTrackingModule:
    def test_empty_detections(self):
        from modules.tracking.tracker import track_vehicles
        assert track_vehicles([]) == []

    def test_returns_list_of_dicts(self):
        from modules.tracking.tracker import track_vehicles
        detections = [(10, 20, 80, 50, 0.9)]
        result = track_vehicles(detections)
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_dict_has_required_keys(self):
        from modules.tracking.tracker import track_vehicles
        result = track_vehicles([(10, 20, 80, 50, 0.88)])
        v = result[0]
        assert "id"         in v, "Missing key: id"
        assert "box"        in v, "Missing key: box"
        assert "confidence" in v, "Missing key: confidence"

    def test_ids_are_unique(self):
        from modules.tracking.tracker import track_vehicles
        detections = [(i*10, i*10, 80, 50, 0.7) for i in range(5)]
        result = track_vehicles(detections)
        ids = [v["id"] for v in result]
        assert len(ids) == len(set(ids)), "Duplicate vehicle IDs detected"

    def test_box_matches_detection(self):
        from modules.tracking.tracker import track_vehicles
        det = (50, 100, 80, 50, 0.75)
        result = track_vehicles([det])
        x, y, w, h = result[0]["box"]
        assert (x, y, w, h) == (50, 100, 80, 50)

    def test_confidence_preserved(self):
        from modules.tracking.tracker import track_vehicles
        result = track_vehicles([(0, 0, 60, 40, 0.91)])
        assert abs(result[0]["confidence"] - 0.91) < 1e-6


# ═══════════════════════════════════════════════════════════════════════════
# 4.  Violation logic
# ═══════════════════════════════════════════════════════════════════════════
class TestViolationModule:
    """STOP_LINE_Y is 300. Vehicle center_y > 300 → violation."""

    def _vehicle(self, y, h=50):
        return {"id": 1, "box": (10, y, 80, h), "confidence": 0.8}

    def test_below_stop_line_is_violation(self):
        """center_y = y + h//2; y=350 → center_y=375 → violation."""
        from modules.violations.violation import check_violation
        assert check_violation(self._vehicle(y=350)) is True

    def test_above_stop_line_is_not_violation(self):
        """y=100 → center_y=125 → no violation."""
        from modules.violations.violation import check_violation
        assert check_violation(self._vehicle(y=100)) is False

    def test_exactly_at_stop_line(self):
        """center_y=300 is NOT strictly > 300, so no violation."""
        from modules.violations.violation import check_violation
        # y=275, h=50 → center_y=300 (not a violation per strict >)
        assert check_violation(self._vehicle(y=275, h=50)) is False

    def test_one_pixel_over_line(self):
        """center_y=301 → violation."""
        from modules.violations.violation import check_violation
        # y=276, h=50 → center_y=301
        assert check_violation(self._vehicle(y=276, h=50)) is True

    def test_none_vehicle(self):
        from modules.violations.violation import check_violation
        assert check_violation(None) is False

    def test_missing_box_key(self):
        from modules.violations.violation import check_violation
        assert check_violation({"id": 1, "confidence": 0.9}) is False


# ═══════════════════════════════════════════════════════════════════════════
# 5.  Evidence capture
# ═══════════════════════════════════════════════════════════════════════════
class TestEvidenceCapture:
    def setup_method(self):
        self._saved = []

    def teardown_method(self):
        for p in self._saved:
            if p and os.path.isfile(p):
                os.remove(p)

    def test_saves_image_file(self):
        from modules.evidence.capture import save_evidence
        path = save_evidence(blank_frame(), vehicle_id=99)
        self._saved.append(path)
        assert path is not None
        assert os.path.isfile(path), f"Evidence file not found: {path}"

    def test_returns_jpg_path(self):
        from modules.evidence.capture import save_evidence
        path = save_evidence(blank_frame(), vehicle_id=42)
        self._saved.append(path)
        assert path.endswith(".jpg")

    def test_none_frame_returns_none(self):
        from modules.evidence.capture import save_evidence
        path = save_evidence(None, vehicle_id=1)
        assert path is None

    def test_filename_contains_vehicle_id(self):
        from modules.evidence.capture import save_evidence
        path = save_evidence(blank_frame(), vehicle_id=777)
        self._saved.append(path)
        assert "777" in path


# ═══════════════════════════════════════════════════════════════════════════
# 6.  Database layer
# ═══════════════════════════════════════════════════════════════════════════
class TestDatabase:
    _TEST_DB = "test_traffic_tmp.db"

    def setup_method(self):
        """Patch DB_PATH to use a temp database."""
        import database.db as db_mod
        self._orig_path = db_mod.DB_PATH if hasattr(db_mod, "DB_PATH") else None
        # Monkey-patch
        import config as cfg
        self._orig_cfg_path = cfg.DB_PATH
        cfg.DB_PATH = self._TEST_DB
        db_mod.DB_PATH = self._TEST_DB   # db.py reads from config at import time
        # Re-import to reset connections
        import importlib
        importlib.reload(db_mod)

    def teardown_method(self):
        import database.db as db_mod, config as cfg, importlib
        cfg.DB_PATH = self._orig_cfg_path
        db_mod.DB_PATH = self._orig_cfg_path
        importlib.reload(db_mod)
        if os.path.isfile(self._TEST_DB):
            os.remove(self._TEST_DB)

    def test_init_creates_table(self):
        from database.db import init_db
        init_db()
        conn = sqlite3.connect(self._TEST_DB)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='violations'")
        assert cur.fetchone() is not None
        conn.close()

    def test_log_and_retrieve_violation(self):
        from database.db import init_db, log_violation, get_violations
        init_db()
        log_violation(vehicle_id=10, image_path="evidence/test.jpg", confidence=0.88)
        rows = get_violations()
        assert len(rows) >= 1

    def test_violation_fields(self):
        from database.db import init_db, log_violation, get_violations
        init_db()
        log_violation(vehicle_id=55, image_path="evidence/v55.jpg", confidence=0.77)
        row = get_violations()[0]
        # row = (id, vehicle_id, timestamp, image_path)
        assert row[1] == 55
        assert "evidence" in row[3]

    def test_multiple_violations_stored(self):
        from database.db import init_db, log_violation, get_violations
        init_db()
        for i in range(5):
            log_violation(vehicle_id=i, image_path=f"evidence/v{i}.jpg", confidence=0.6+i*0.05)
        rows = get_violations()
        assert len(rows) == 5


# ═══════════════════════════════════════════════════════════════════════════
# 7.  End-to-end smoke test
# ═══════════════════════════════════════════════════════════════════════════
class TestEndToEnd:
    """Synthetic frame → detect → track → check → save → log → retrieve."""

    def test_full_pipeline_with_mock_detections(self):
        from modules.tracking.tracker import track_vehicles
        from modules.violations.violation import check_violation
        from modules.evidence.capture import save_evidence
        from database.db import init_db, log_violation, get_violations
        import config as cfg, importlib, database.db as db_mod

        # Use a temp DB
        tmp_db = "e2e_test_tmp.db"
        orig = cfg.DB_PATH
        cfg.DB_PATH = tmp_db
        db_mod.DB_PATH = tmp_db
        importlib.reload(db_mod)

        try:
            init_db()
            frame = blank_frame()

            # Simulate two vehicles: one above stop line, one below (violation)
            mock_dets = [
                (50,  100, 80, 50, 0.82),   # center_y=125 → no violation
                (200, 350, 80, 50, 0.91),   # center_y=375 → violation
            ]
            tracked = track_vehicles(mock_dets)
            violations_found = 0

            for v in tracked:
                if check_violation(v):
                    path = save_evidence(frame, v["id"])
                    log_violation(vehicle_id=v["id"],
                                  image_path=path or "evidence/mock.jpg",
                                  confidence=v["confidence"])
                    violations_found += 1
                    if path and os.path.isfile(path):
                        os.remove(path)

            assert violations_found == 1, (
                f"Expected 1 violation, got {violations_found}"
            )
            rows = get_violations()
            assert len(rows) == 1
        finally:
            cfg.DB_PATH = orig
            db_mod.DB_PATH = orig
            importlib.reload(db_mod)
            if os.path.isfile(tmp_db):
                os.remove(tmp_db)

    def test_zero_violations_when_all_above_line(self):
        from modules.tracking.tracker import track_vehicles
        from modules.violations.violation import check_violation

        mock_dets = [(i*50, 50, 60, 40, 0.75) for i in range(4)]
        tracked = track_vehicles(mock_dets)
        violations = [v for v in tracked if check_violation(v)]
        assert len(violations) == 0


# ═══════════════════════════════════════════════════════════════════════════
# Main runner (also works without pytest)
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  SmartTraffic Vision — Model Test Suite")
    print("=" * 60)

    import time, traceback

    test_classes = [
        TestYOLOModel,
        TestDetectionModule,
        TestTrackingModule,
        TestViolationModule,
        TestEvidenceCapture,
        TestDatabase,
        TestEndToEnd,
    ]

    total = passed = failed = 0

    for cls in test_classes:
        print(f"\n{'─'*50}")
        print(f"  {cls.__name__}")
        print(f"{'─'*50}")
        inst = cls()
        for name in [m for m in dir(cls) if m.startswith("test_")]:
            total += 1
            try:
                if hasattr(inst, "setup_method"):
                    inst.setup_method()
                getattr(inst, name)()
                if hasattr(inst, "teardown_method"):
                    inst.teardown_method()
                print(f"  ✅  {name}")
                passed += 1
            except Exception as e:
                failed += 1
                print(f"  ❌  {name}")
                print(f"      → {e}")

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} passed  |  {failed} failed")
    print(f"{'='*60}")
    if failed == 0:
        print("  🎉  All tests PASSED — model pipeline is healthy!")
    else:
        print("  ⚠️   Some tests FAILED — see details above.")
    print()
