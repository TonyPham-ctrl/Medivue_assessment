import sqlite3
import contextlib
from src.config import DB_PATH, DB_PATIENT_GLUCOSE_TABLE


class PatientGlucoseService:
    def __init__(self):
        self.db_path = DB_PATH

    def save_patient_glucose(self, patient_glucose):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute(f"""
                    INSERT OR REPLACE INTO {DB_PATIENT_GLUCOSE_TABLE} (
                        patient_id, lower_bound, upper_bound
                    )
                    VALUES (?, ?, ?)
                """, (
                    patient_glucose.patient_id,
                    patient_glucose.lower_bound,
                    patient_glucose.upper_bound
                ))

    def query_patient_glucose(self, patient_id: str):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT lower_bound, upper_bound
                FROM {DB_PATIENT_GLUCOSE_TABLE}
                WHERE patient_id = ?
            """, (patient_id,))
            return cursor.fetchone()


patient_glucose_service = PatientGlucoseService()
