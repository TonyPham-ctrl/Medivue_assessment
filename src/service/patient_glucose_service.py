import sqlite3
from src.storage.sqlite_db import PATIENT_GLUCOSE_PATH, PATIENT_GLUCOSE_DB


class PatientGlucoseService:
    def __init__(self):
        self.db_path = PATIENT_GLUCOSE_PATH

    def save_patient_glucose(self, patient_glucose):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT OR REPLACE INTO {PATIENT_GLUCOSE_DB} (
                patient_id, lower_bound, upper_bound
            )
            VALUES (?, ?, ?)
        """, (
            patient_glucose.patient_id,
            patient_glucose.lower_bound,
            patient_glucose.upper_bound
        ))
        conn.commit()
        conn.close()

    def query_patient_glucose(self, patient_id: str):
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


patient_glucose_service = PatientGlucoseService()
