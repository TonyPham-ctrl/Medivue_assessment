import math
import sqlite3
import contextlib
from datetime import datetime
from src.config import DB_PATH, DB_READING_TABLE, STAT_MIN_SAMPLES


class StorageService:
    def __init__(self):
        self.db_path = DB_PATH

    def save_reading(self, payload):
        r = payload.reading
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute(f"""
                    INSERT INTO {DB_READING_TABLE} (
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

    def get_patient_glucose_stats(self, patient_id: str, exclude_timestamp: datetime = None):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            if exclude_timestamp:
                cursor.execute(f"""
                    SELECT COUNT(*), AVG(glucose), AVG(glucose * glucose)
                    FROM {DB_READING_TABLE}
                    WHERE patient_id = ? AND recorded_at != ?
                """, (patient_id, exclude_timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            else:
                cursor.execute(f"""
                    SELECT COUNT(*), AVG(glucose), AVG(glucose * glucose)
                    FROM {DB_READING_TABLE} WHERE patient_id = ?
                """, (patient_id,))
            n, avg, avg_sq = cursor.fetchone()
        if not n or n < STAT_MIN_SAMPLES:
            return None
        pop_var = avg_sq - avg * avg
        sample_std = math.sqrt(max(0.0, pop_var * n / (n - 1)))
        return avg, sample_std

    def has_duplicate(self, device_id: str, recorded_at: datetime) -> bool:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 1 FROM {DB_READING_TABLE}
                WHERE device_id = ? AND recorded_at = ?
                LIMIT 1
            """, (device_id, recorded_at.strftime("%Y-%m-%d %H:%M:%S")))
            row = cursor.fetchone()
        return row is not None

    def query_readings(self, patient_id: str, n: int = 12):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT device_id, glucose, battery_pct, signal_quality, recorded_at
                FROM {DB_READING_TABLE}
                WHERE patient_id = ?
                ORDER BY recorded_at DESC
                LIMIT ?
            """, (patient_id, n))
            readings = [dict(row) for row in cursor.fetchall()]
        return readings


storage_service = StorageService()
