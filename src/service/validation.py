from src.models.enums import IngestionStatus, AlertType
from src.service.storage_service import storage_service
from src.service.patient_glucose_service import patient_glucose_service
from src.config import VALID_SIGNAL_QUALITIES, BATTERY_PCT_MIN, BATTERY_PCT_MAX, GLUCOSE_MGDL_MIN, STAT_ANOMALY_STDDEV_MULTIPLIER


class ValidationService:

    def validate_post_payload(self, payload):
        response_message = ""
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

        if storage_service.has_duplicate(payload.device_id, payload.reading.recorded_at):
            response_message += "Duplicate reading detected \n"
            response_status = IngestionStatus.DUPLICATE

        return response_status, response_message

    def check_thresholds(self, payload) -> AlertType:
        threshold = patient_glucose_service.query_patient_glucose(payload.patient_id)
        if not threshold:
            return AlertType.UNKNOWN_GLUCOSE

        lower_bound, upper_bound = threshold
        glucose = payload.reading.glucose_mgdl

        if glucose < lower_bound:
            return AlertType.LOW_GLUCOSE
        elif glucose > upper_bound:
            return AlertType.HIGH_GLUCOSE

        stats = storage_service.get_patient_glucose_stats(payload.patient_id, payload.reading.recorded_at)
        if stats:
            mean, stdev = stats
            if stdev > 0 and abs(glucose - mean) > STAT_ANOMALY_STDDEV_MULTIPLIER * stdev:
                return AlertType.GLUCOSE_SPIKE if glucose > mean else AlertType.GLUCOSE_DROP

        return AlertType.NORMAL


validation_service = ValidationService()
