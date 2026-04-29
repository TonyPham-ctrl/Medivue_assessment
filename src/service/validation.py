from src.service.storage_service import PatientGlucoseService, StorageService
from src.models.enums import IngestionStatus, ThresholdStatus
from src.config import VALID_SIGNAL_QUALITIES, BATTERY_PCT_MIN, BATTERY_PCT_MAX, GLUCOSE_MGDL_MIN


def is_duplicate(device_id, recorded_at):
    readings = StorageService().get_readings_by_device(device_id)
    return any(str(reading[5]) == str(recorded_at) for reading in readings)

def validate_post_payload(payload):
    response_message = "Success"
    response_status = IngestionStatus.SUCCESS
    if not payload.device_id or not isinstance(payload.device_id, str):
        response_message += "device_id must be a non-empty string \n"
        response_status = IngestionStatus.INVALID

    if not payload.patient_id or not isinstance(payload.patient_id, str):
        response_message += "patient_id must be a non-empty string \n"
        response_status = IngestionStatus.INVALID

    if payload.reading.glucose_mgdl <= GLUCOSE_MGDL_MIN:
        response_message += f"glucose_mgdl must be greater than {GLUCOSE_MGDL_MIN} \n"
        response_status = IngestionStatus.INVALID

    if not (BATTERY_PCT_MIN <= payload.reading.battery_pct <= BATTERY_PCT_MAX):
        response_message += f"battery_pct must be between {BATTERY_PCT_MIN} and {BATTERY_PCT_MAX} \n"
        response_status = IngestionStatus.INVALID

    if payload.reading.signal_quality not in VALID_SIGNAL_QUALITIES:
        response_message += f"signal_quality must be one of {VALID_SIGNAL_QUALITIES} \n"
        response_status = IngestionStatus.INVALID

    if is_duplicate(payload.device_id, payload.reading.recorded_at):
        response_message += "Duplicate reading detected \n"
        response_status = IngestionStatus.DUPLICATE

    return response_status, response_message


def check_thresholds(payload):
    patient_glucose_threshold = PatientGlucoseService().query_patient_glucose(payload.patient_id)
    if not patient_glucose_threshold:
        return ThresholdStatus.UNKNOWN

    lower_bound, upper_bound = patient_glucose_threshold

    if payload.reading.glucose_mgdl < lower_bound:
        return ThresholdStatus.LOW
    elif payload.reading.glucose_mgdl > upper_bound:
        return ThresholdStatus.HIGH

    return ThresholdStatus.NORMAL