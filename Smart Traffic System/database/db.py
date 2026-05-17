# database/db.py
import sqlite3
import datetime
from config import DB_PATH
import logging

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            timestamp TEXT,
            image_path TEXT,
            confidence REAL DEFAULT 0.0,
            violation_type TEXT DEFAULT 'stop_line',
            plate_number TEXT DEFAULT NULL
        )
    ''')
    # Add plate_number column to existing DBs that pre-date this change
    try:
        cursor.execute("ALTER TABLE violations ADD COLUMN plate_number TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

def log_violation(vehicle_id, image_path, confidence=0.0,
                  violation_type="stop_line", plate_number=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO violations
        (vehicle_id, timestamp, image_path, confidence, violation_type, plate_number)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (vehicle_id, timestamp, image_path, confidence, violation_type, plate_number))
    conn.commit()
    conn.close()
    plate_info = f" | Plate: {plate_number}" if plate_number else ""
    logging.info(f"Violation logged - Vehicle {vehicle_id} | Confidence {confidence}{plate_info}")

def get_violations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, vehicle_id, timestamp, image_path, plate_number '
        'FROM violations ORDER BY id DESC'
    )
    rows = cursor.fetchall()
    conn.close()
    return rows