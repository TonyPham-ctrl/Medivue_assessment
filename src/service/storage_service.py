import sqlite3
from datetime import datetime
from src.storage.sqlite_db import READING_PATH, READING_DB


class StorageService:
    def __init__(self):
        self.db_path = READING_PATH

    def save_reading(self, payload):
        r = payload.reading
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {READING_DB} (
                device_id, patient_id, glucose, battery_pct, signal_quality, recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            payload.device_id,
            payload.patient_id,
            r.glucose_mgdl,
            r.battery_pct,
            r.signal_quality,
            r.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()

    def query_readings(self, patient_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT device_id, patient_id, glucose, battery_pct, signal_quality, recorded_at
            FROM {READING_DB}
            WHERE patient_id = ?
            ORDER BY recorded_at DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def has_duplicate(self, device_id: str, recorded_at: datetime) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 1 FROM {READING_DB}
            WHERE device_id = ? AND recorded_at = ?
            LIMIT 1
        """, (device_id, recorded_at.strftime("%Y-%m-%d %H:%M:%S")))
        row = cursor.fetchone()
        conn.close()
        return row is not None


storage_service = StorageService()
