
from typing import List
from src.models.payload import ExportPayload
from src.service.storage_service import StorageService
from src.storage.session_memory import session_memory

class ExportService:

    def calculate_percentage_in_range(self, readings: List) -> float:
        if not readings:
            return 0.0
        in_range_count = sum(1 for r in readings if 70 <= r['glucose_mgdl'] <= 180)
        return (in_range_count / len(readings)) * 100
    
    def construct_reading_payload(self, reading: dict):
        return ExportPayload.ReadingPayload(
            glucose_mgdl=reading['glucose_mgdl'],
            battery_pct=reading['battery_pct'],
            signal_quality=reading['signal_quality'],
            recorded_at=reading['recorded_at']
        )
    
    def construct_export_payload(self, patient_id: str, readings: List):        
        alerts = session_memory.get_alerts(patient_id)
        most_recent_alert = alerts[-1] if alerts else None
        print(most_recent_alert)
        return ExportPayload(
            device_id=readings[0]['device_id'],
            patient_id=patient_id,
            battery_pct=readings[0]['battery_pct'],
            signal_quality=readings[0]['signal_quality'],
            alert_status=most_recent_alert._get_alert_type(),
            percentage_in_range=self.calculate_percentage_in_range(readings),
            summary=self.construct_reading_payload(readings[0])
        )

    def process(self, patient_id: str):
        readings = StorageService().query_readings(patient_id)
        if not readings:
            raise ValueError(f"No readings found for patient_id: {patient_id}")
        return self.construct_export_payload(patient_id, readings)

