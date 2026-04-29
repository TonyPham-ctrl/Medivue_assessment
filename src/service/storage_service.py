import sqlite3
from src.storage.sqlite_db import READING_PATH, PATIENT_GLUCOSE_PATH

class StorageService:
    def __init__(self):
        self.db_path = READING_PATH

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
    
class PatientGlucoseService:
    def __init__(self):
        self.db_path = PATIENT_GLUCOSE_PATH

    def save_patient_glucose(self, patient_glucose):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO patient_glucose (
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
    
    def get_patient_glucose(self, patient_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT patient_id, lower_bound, upper_bound
            FROM patient_glucose
            WHERE patient_id = ?
        """, (patient_id,))

        row = cursor.fetchone()
        conn.close()

        return row
    
    def check_glucose_status(self, patient_id, glucose_value):
        patient_glucose = self.get_patient_glucose(patient_id)
        if not patient_glucose:
            return "unknown"

        _, lower_bound, upper_bound = patient_glucose

        if glucose_value < lower_bound:
            return "low"
        elif glucose_value > upper_bound:
            return "high"
        return "normal"