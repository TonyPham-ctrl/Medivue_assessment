import sqlite3
from src.storage.sqlite_db import READING_PATH, PATIENT_GLUCOSE_PATH, READING_DB, PATIENT_GLUCOSE_DB

class StorageService:
    def __init__(self):
        self.db_path = READING_PATH

    def save_reading(self, payload):
        r = payload.reading

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            INSERT INTO {READING_DB} (
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

    def query_readings(self, patient_id):
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

    def get_readings_by_device(self, device_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT device_id, patient_id, glucose, battery_pct, signal_quality, recorded_at
            FROM {READING_DB}
            WHERE device_id = ?
            ORDER BY recorded_at DESC
        """, (device_id,))

        rows = cursor.fetchall()
        conn.close()

        return rows
    
class PatientGlucoseService:
    def __init__(self):
        self.db_path = PATIENT_GLUCOSE_PATH

    def save_patient_glucose(self, patient_glucose):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            INSERT OR REPLACE INTO {PATIENT_GLUCOSE_DB} (
                patient_id,
                lower_bound,
                upper_bound
            )
            VALUES (?, ?, ?)
        """, (
            patient_glucose.patient_id,
            patient_glucose.lower_bound,
            patient_glucose.upper_bound
        ))

        conn.commit()
        conn.close()

    def query_patient_glucose(self, patient_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT lower_bound, upper_bound
            FROM {PATIENT_GLUCOSE_DB}
            WHERE patient_id = ?
        """, (patient_id,))

        row = cursor.fetchone()
        conn.close()

        return row
    
