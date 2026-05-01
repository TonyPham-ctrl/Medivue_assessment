import math
import sqlite3
import contextlib
from datetime import datetime, timedelta
from src.config import DB_PATH, DB_READING_TABLE, DB_PATIENT_GLUCOSE_TABLE, STAT_MIN_SAMPLES


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

    def get_recent_glucose_readings(self, patient_id: str, reference_time: datetime, minutes: int) -> list[tuple[float, str]]:
        cutoff = (reference_time - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT glucose, recorded_at FROM {DB_READING_TABLE}
                WHERE patient_id = ? AND recorded_at >= ?
                ORDER BY recorded_at ASC
            """, (patient_id, cutoff))
            return cursor.fetchall()

    def get_last_reading_time(self, device_id: str, before_time: datetime) -> datetime | None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT recorded_at FROM {DB_READING_TABLE}
                WHERE device_id = ? AND recorded_at < ?
                ORDER BY recorded_at DESC LIMIT 1
            """, (device_id, before_time.strftime("%Y-%m-%d %H:%M:%S")))
            row = cursor.fetchone()
        if row:
            return datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        return None

    def get_recent_signal_qualities(self, device_id: str, count: int) -> list[str]:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT signal_quality FROM {DB_READING_TABLE}
                WHERE device_id = ?
                ORDER BY recorded_at DESC LIMIT ?
            """, (device_id, count))
            return [row[0] for row in cursor.fetchall()]

    def get_patient_glucose_bounds(self, patient_id: str) -> tuple[float, float] | None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT lower_bound, upper_bound FROM {DB_PATIENT_GLUCOSE_TABLE}
                WHERE patient_id = ?
            """, (patient_id,))
            row = cursor.fetchone()
        return (row[0], row[1]) if row else None

    def query_readings(self, patient_id: str):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT device_id, patient_id, glucose, battery_pct, signal_quality, recorded_at
                FROM {DB_READING_TABLE}
                WHERE patient_id = ?
                AND recorded_at >= datetime('now', '-1 day')
                ORDER BY recorded_at DESC
            """, (patient_id,))

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

storage_service = StorageService()
