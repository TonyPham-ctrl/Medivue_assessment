from src.service.storage_service import PatientGlucoseService, StorageService
from src.storage.sqlite_db import READING_PATH, PATIENT_GLUCOSE_PATH
from src.models.enums import IngestionStatus, ThresholdStatus


def is_duplicate(device_id, recorded_at):
    readings = StorageService().get_readings(device_id)
    return any(str(reading[5]) == str(recorded_at) for reading in readings)

def validate_post_payload(payload):
    response_message = ""
    response_status = IngestionStatus.SUCCESS
    if not payload.device_id or not isinstance(payload.device_id, str):
        response_message += "device_id must be a non-empty string \n"
        response_status = IngestionStatus.INVALID

    if not payload.patient_id or not isinstance(payload.patient_id, str):
        response_message += "patient_id must be a non-empty string \n"
        response_status = IngestionStatus.INVALID

    if payload.reading.glucose_mgdl <= 0:
        response_message += "glucose_mgdl must be a positive number \n"
        response_status = IngestionStatus.INVALID

    if not (0 <= payload.reading.battery_pct <= 100):
        response_message += "battery_pct must be between 0 and 100 \n"
        response_status = IngestionStatus.INVALID

    if payload.reading.signal_quality not in ["good", "poor", "degraded"]:
        response_message += "signal_quality must be 'good', 'poor', or 'degraded' \n"
        response_status = IngestionStatus.INVALID

    if is_duplicate(payload.device_id, payload.reading.recorded_at):
        response_message += "Duplicate reading detected \n"
        response_status = IngestionStatus.DUPLICATE

    return response_status, response_message


def check_thresholds(payload):
    patient_glucose_threshold = PatientGlucoseService().query_patient_glucose_patient_glucose(payload.patient_id)
    if not patient_glucose_threshold:
        return ThresholdStatus.UNKNOWN

    lower_bound, upper_bound = patient_glucose_threshold

    if payload.reading.glucose_mgdl < lower_bound:
        return ThresholdStatus.LOW
    elif payload.reading.glucose_mgdl > upper_bound:
        return ThresholdStatus.HIGH

    return ThresholdStatus.NORMAL