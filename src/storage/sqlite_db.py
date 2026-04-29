import sqlite3
from src.config import DB_READING_PATH, DB_PATIENT_GLUCOSE_PATH, DB_READING_TABLE, DB_PATIENT_GLUCOSE_TABLE

READING_PATH = DB_READING_PATH
PATIENT_GLUCOSE_PATH = DB_PATIENT_GLUCOSE_PATH

READING_DB = DB_READING_TABLE
PATIENT_GLUCOSE_DB = DB_PATIENT_GLUCOSE_TABLE

def init_readings_table():
    conn = sqlite3.connect(READING_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            patient_id TEXT,
            glucose REAL,
            battery_pct INTEGER,
            signal_quality TEXT,
            recorded_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def init_patient_glucose_table():
    conn = sqlite3.connect(PATIENT_GLUCOSE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_glucose (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE,
            lower_bound REAL,
            upper_bound REAL
        )
    """)

    conn.commit()
    conn.close()