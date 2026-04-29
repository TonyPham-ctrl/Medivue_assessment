import math
import sqlite3
from datetime import datetime
from src.storage.sqlite_db import READING_PATH, READING_DB
from src.config import STAT_MIN_SAMPLES


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


    def get_patient_glucose_stats(self, patient_id: str, exclude_timestamp: datetime = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if exclude_timestamp:
            cursor.execute(f"""
                SELECT COUNT(*), AVG(glucose), AVG(glucose * glucose)
                FROM {READING_DB}
                WHERE patient_id = ? AND recorded_at != ?
            """, (patient_id, exclude_timestamp.strftime("%Y-%m-%d %H:%M:%S")))
        else:
            cursor.execute(f"""
                SELECT COUNT(*), AVG(glucose), AVG(glucose * glucose)
                FROM {READING_DB} WHERE patient_id = ?
            """, (patient_id,))
        n, avg, avg_sq = cursor.fetchone()
        conn.close()
        if not n or n < STAT_MIN_SAMPLES:
            return None
        # sample standard deviation via aggregate moments: avoids fetching all rows
        pop_var = avg_sq - avg * avg
        sample_std = math.sqrt(max(0.0, pop_var * n / (n - 1)))
        return avg, sample_std

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
