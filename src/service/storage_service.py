import sqlite3
from src.storage.sqlite_db import DB_PATH

class StorageService:
    def __init__(self):
        self.db_path = DB_PATH

    def save_reading(self, payload):
        r = payload.reading

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO readings (
                device_id,
                patient_id,
                glucose,
                battery_pct,
                signal_quality,
                recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            payload.device_id,
            payload.patient_id,
            r.glucose_mgdl,
            r.battery_pct,
            r.signal_quality,
            str(r.recorded_at)
        ))

        conn.commit()
        conn.close()

    def get_readings(self, patient_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT device_id, patient_id, glucose, battery_pct, signal_quality, recorded_at
            FROM readings
            WHERE patient_id = ?
            ORDER BY recorded_at DESC
        """, (patient_id,))

        rows = cursor.fetchall()
        conn.close()

        return rows