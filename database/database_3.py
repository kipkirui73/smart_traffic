"""
SmartTraffic Vision - Database Module

Handles all database operations using SQLite.
Provides: create_tables(), insert_violation(), query_violations()
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "smarttraffic.db")


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like row access
    return conn


def create_tables():
    """
    Create all required database tables if they do not already exist.
    Tables: cameras, vehicles, violations, evidence, users
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS cameras (
            camera_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            location    TEXT    NOT NULL,
            stream_url  TEXT    NOT NULL,
            status      TEXT    DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_type TEXT    NOT NULL,
            camera_id    INTEGER NOT NULL,
            first_seen   TEXT    NOT NULL,
            FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
        );

        CREATE TABLE IF NOT EXISTS violations (
            violation_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id      INTEGER NOT NULL,
            camera_id       INTEGER NOT NULL,
            violation_type  TEXT    NOT NULL,
            timestamp       TEXT    NOT NULL,
            location        TEXT    NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
            FOREIGN KEY (camera_id)  REFERENCES cameras(camera_id)
        );

        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_id INTEGER NOT NULL,
            file_path    TEXT    NOT NULL,
            file_type    TEXT    NOT NULL CHECK(file_type IN ('image', 'video')),
            captured_at  TEXT    NOT NULL,
            FOREIGN KEY (violation_id) REFERENCES violations(violation_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            role      TEXT    NOT NULL DEFAULT 'officer'
        );
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables created (or already exist).")


def insert_violation(vehicle_id, camera_id, violation_type, location,
                     image_path=None, timestamp=None):
    """
    Insert a new violation record and optionally attach image evidence.

    Parameters:
        vehicle_id     (int)  : ID of the detected vehicle
        camera_id      (int)  : ID of the camera that captured it
        violation_type (str)  : 'signal_jumping' or 'wrong_way_driving'
        location       (str)  : Human-readable location label
        image_path     (str)  : Path to the saved evidence image (optional)
        timestamp      (str)  : ISO timestamp; defaults to current time

    Returns:
        int: The ID of the newly inserted violation record
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO violations (vehicle_id, camera_id, violation_type, timestamp, location)
        VALUES (?, ?, ?, ?, ?)
        """,
        (vehicle_id, camera_id, violation_type, timestamp, location)
    )
    violation_id = cursor.lastrowid

    if image_path:
        cursor.execute(
            """
            INSERT INTO evidence (violation_id, file_path, file_type, captured_at)
            VALUES (?, ?, 'image', ?)
            """,
            (violation_id, image_path, timestamp)
        )

    conn.commit()
    conn.close()
    print(f"[DB] Violation #{violation_id} inserted ({violation_type}).")
    return violation_id


def query_violations(limit=50, violation_type=None, camera_id=None,
                     start_date=None, end_date=None):
    """
    Query violation records with optional filters.

    Parameters:
        limit          (int)  : Max number of records to return (default 50)
        violation_type (str)  : Filter by violation type (optional)
        camera_id      (int)  : Filter by camera ID (optional)
        start_date     (str)  : ISO date string, e.g. '2025-06-01' (optional)
        end_date       (str)  : ISO date string, e.g. '2025-06-30' (optional)

    Returns:
        list[dict]: List of violation records as dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT  v.violation_id,
                v.vehicle_id,
                v.camera_id,
                v.violation_type,
                v.timestamp,
                v.location,
                e.file_path  AS evidence_path
        FROM    violations v
        LEFT JOIN evidence e ON v.violation_id = e.violation_id
        WHERE 1=1
    """
    params = []

    if violation_type:
        query += " AND v.violation_type = ?"
        params.append(violation_type)
    if camera_id:
        query += " AND v.camera_id = ?"
        params.append(camera_id)
    if start_date:
        query += " AND v.timestamp >= ?"
        params.append(start_date)
    if end_date:
        query += " AND v.timestamp <= ?"
        params.append(end_date + " 23:59:59")

    query += " ORDER BY v.timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_summary_stats():
    """
    Return dashboard summary counts.

    Returns:
        dict with keys: total_violations, signal_jumping,
                        wrong_way_driving, active_cameras
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM violations")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM violations WHERE violation_type = 'signal_jumping'")
    signal = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM violations WHERE violation_type = 'wrong_way_driving'")
    wrong_way = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cameras WHERE status = 'active'")
    cameras = cursor.fetchone()[0]

    conn.close()
    return {
        "total_violations": total,
        "signal_jumping": signal,
        "wrong_way_driving": wrong_way,
        "active_cameras": cameras,
    }


def insert_camera(location, stream_url, status="active"):
    """Insert a new camera record. Returns camera_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cameras (location, stream_url, status) VALUES (?, ?, ?)",
        (location, stream_url, status)
    )
    cam_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cam_id


def get_cameras():
    """Return all camera records as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cameras")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_violation(violation_id):
    """Delete a violation and its linked evidence records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evidence  WHERE violation_id = ?", (violation_id,))
    cursor.execute("DELETE FROM violations WHERE violation_id = ?", (violation_id,))
    conn.commit()
    conn.close()
    print(f"[DB] Violation #{violation_id} deleted.")


if __name__ == "__main__":
    create_tables()
    print("[DB] SmartTraffic Vision database initialized successfully.")
