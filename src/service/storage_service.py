import sqlite3
from src.storage.sqlite_db import READING_PATH, PATIENT_GLUCOSE_PATH, READING_DB, PATIENT_GLUCOSE_DB

class StorageService:
    def __init__(self):
        self.db_path = READING_PATH

    def save_reading(self, payload):
        r = payload.reading

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO {} (
                device_id,
                patient_id,
                glucose,
                battery_pct,
                signal_quality,
                recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            READING_DB,
            payload.device_id,
            payload.patient_id,
            r.glucose_mgdl,
            r.battery_pct,
            r.signal_quality,
            str(r.recorded_at)
        ))

        conn.commit()
        conn.close()

    def query_readings(self, patient_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT device_id, patient_id, glucose, battery_pct, signal_quality, recorded_at
            FROM {}
            WHERE patient_id = ?
            ORDER BY recorded_at DESC
        """, (READING_DB, patient_id))

        rows = cursor.fetchall()
        conn.close()

        return rows
    
class PatientGlucoseService:
    def __init__(self):
        self.db_path = PATIENT_GLUCOSE_PATH

    def save_patient_glucose(self, patient_glucose):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO {} (
                patient_id,
                lower_bound,
                upper_bound
            )
            VALUES (?, ?, ?)
        """, (
            PATIENT_GLUCOSE_DB,
            patient_glucose.patient_id,
            patient_glucose.lower_bound,
            patient_glucose.upper_bound
        ))

        conn.commit()
        conn.close()
    
    def query_patient_glucose(self, patient_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT lower_bound, upper_bound
            FROM {}
            WHERE patient_id = ?
        """, (PATIENT_GLUCOSE_DB, patient_id))

        row = cursor.fetchone()
        conn.close()

        return row
    
