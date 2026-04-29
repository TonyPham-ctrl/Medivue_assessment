import sqlite3
import contextlib
from src.config import DB_PATH, DB_READING_TABLE, DB_PATIENT_GLUCOSE_TABLE


def init_db():
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_READING_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    patient_id TEXT,
                    glucose REAL,
                    battery_pct INTEGER,
                    signal_quality TEXT,
                    recorded_at DATETIME
                )
            """)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_readings_device_time
                ON {DB_READING_TABLE} (device_id, recorded_at)
            """)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_readings_patient
                ON {DB_READING_TABLE} (patient_id)
            """)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_PATIENT_GLUCOSE_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE,
                    lower_bound REAL,
                    upper_bound REAL
                )
            """)
