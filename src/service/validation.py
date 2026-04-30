from src.models.enums import IngestionStatus, AlertType
from src.service.storage_service import storage_service
from src.config import (
    VALID_SIGNAL_QUALITIES, GLUCOSE_MGDL_MIN,
    GLUCOSE_CRITICAL_LOW, GLUCOSE_LOW, GLUCOSE_HIGH, GLUCOSE_CRITICAL_HIGH,
    BATTERY_PCT_LOW_THRESHOLD, BATTERY_PCT_CRITICAL_THRESHOLD,
    STAT_ANOMALY_STDDEV_MULTIPLIER,
    SUSTAINED_HYPO_MINUTES, SUSTAINED_HYPER_MINUTES, SUSTAINED_HYPER_MIN_READINGS,
    RAPID_DROP_MGDL, RAPID_DROP_MINUTES, RAPID_RISE_MGDL, RAPID_RISE_MINUTES,
    SIGNAL_POOR_STREAK_COUNT, DEVICE_OFFLINE_MINUTES,
)


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

        if payload.reading.signal_quality not in VALID_SIGNAL_QUALITIES:
            response_message += f"signal_quality must be one of {VALID_SIGNAL_QUALITIES} \n"
            response_status = IngestionStatus.INVALID

        if storage_service.has_duplicate(payload.device_id, payload.reading.recorded_at):
            response_message += "Duplicate reading detected \n"
            response_status = IngestionStatus.DUPLICATE

        return response_status, response_message

    def check_glucose_threshold(self, payload) -> AlertType:
        glucose = payload.reading.glucose_mgdl
        if glucose < GLUCOSE_CRITICAL_LOW:
            return AlertType.CRITICAL_LOW_GLUCOSE
        if glucose < GLUCOSE_LOW:
            return AlertType.LOW_GLUCOSE
        if glucose > GLUCOSE_CRITICAL_HIGH:
            return AlertType.CRITICAL_HIGH_GLUCOSE
        if glucose > GLUCOSE_HIGH:
            return AlertType.HIGH_GLUCOSE
        return AlertType.NORMAL

    def check_glucose_trend(self, payload) -> AlertType:
        glucose = payload.reading.glucose_mgdl
        ref_time = payload.reading.recorded_at

        recent_drop = storage_service.get_recent_glucose_readings(payload.patient_id, ref_time, RAPID_DROP_MINUTES)
        if len(recent_drop) >= 2 and recent_drop[0][0] - glucose > RAPID_DROP_MGDL:
            return AlertType.RAPID_DROP

        recent_rise = storage_service.get_recent_glucose_readings(payload.patient_id, ref_time, RAPID_RISE_MINUTES)
        if len(recent_rise) >= 2 and glucose - recent_rise[0][0] > RAPID_RISE_MGDL:
            return AlertType.RAPID_RISE

        stats = storage_service.get_patient_glucose_stats(payload.patient_id, ref_time)
        if stats:
            mean, stdev = stats
            if stdev > 0 and abs(glucose - mean) > STAT_ANOMALY_STDDEV_MULTIPLIER * stdev:
                return AlertType.GLUCOSE_SPIKE if glucose > mean else AlertType.GLUCOSE_DROP

        return AlertType.NORMAL

    def check_sustained_glucose(self, payload) -> AlertType:
        glucose = payload.reading.glucose_mgdl
        ref_time = payload.reading.recorded_at

        if glucose < GLUCOSE_LOW:
            recent = storage_service.get_recent_glucose_readings(payload.patient_id, ref_time, SUSTAINED_HYPO_MINUTES)
            if len(recent) >= 2 and all(r[0] < GLUCOSE_LOW for r in recent):
                return AlertType.PERSISTENT_HYPOGLYCEMIA

        if glucose > GLUCOSE_HIGH:
            recent = storage_service.get_recent_glucose_readings(payload.patient_id, ref_time, SUSTAINED_HYPER_MINUTES)
            high = [r for r in recent if r[0] > GLUCOSE_HIGH]
            if len(high) >= SUSTAINED_HYPER_MIN_READINGS:
                return AlertType.PERSISTENT_HYPERGLYCEMIA

        return AlertType.NORMAL

    def check_battery_level(self, payload) -> AlertType:
        batt = payload.reading.battery_pct
        if batt <= BATTERY_PCT_CRITICAL_THRESHOLD:
            return AlertType.CRITICAL_BATTERY
        if batt <= BATTERY_PCT_LOW_THRESHOLD:
            return AlertType.LOW_BATTERY
        return AlertType.NORMAL

    def check_device_health(self, payload) -> AlertType:
        recent_signals = storage_service.get_recent_signal_qualities(payload.device_id, SIGNAL_POOR_STREAK_COUNT)
        if len(recent_signals) >= SIGNAL_POOR_STREAK_COUNT and all(s in ("poor", "degraded") for s in recent_signals):
            return AlertType.SENSOR_DEGRADED

        last_time = storage_service.get_last_reading_time(payload.device_id, payload.reading.recorded_at)
        if last_time:
            gap_minutes = (payload.reading.recorded_at - last_time).total_seconds() / 60
            if gap_minutes > DEVICE_OFFLINE_MINUTES:
                return AlertType.DEVICE_OFFLINE

        return AlertType.NORMAL


validation_service = ValidationService()
