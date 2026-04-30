from src.models.payload import ReadingWrapper
from src.models.enums import IngestionStatus, AlertType
from src.service.validation import validation_service
from src.service.storage_service import storage_service
from src.service.alert import Alert, GlucoseAlert, ValidationAlert, BatteryAlert, DeviceHealthAlert
from src.service.alert_state import alert_state_tracker
from src.storage.session_memory import session_memory


class IngestionService:

    async def _dispatch_alert(self, alert: Alert) -> str:
        await session_memory.add_alert(alert.patient_id, alert)
        return alert.send_alert()

    async def _maybe_fire(self, patient_id: str, category: str, state: AlertType, now, alert: Alert, response: dict, key: str):
        if alert_state_tracker.should_fire(patient_id, category, state, now):
            alert_state_tracker.record_fired(patient_id, category, state, now)
            response[key] = await self._dispatch_alert(alert)
        else:
            alert_state_tracker.update_state(patient_id, category, state)

    async def process(self, payload: ReadingWrapper):
        validation_status, validation_message = validation_service.validate_post_payload(payload)

        if validation_status != IngestionStatus.SUCCESS:
            alert_message = await self._dispatch_alert(
                ValidationAlert(payload.patient_id, str(payload.reading.recorded_at), validation_message)
            )
            return validation_status, {"message": validation_message, "alert": alert_message}

        storage_service.save_reading(payload)

        pid = payload.patient_id
        did = payload.device_id
        ts = payload.reading.recorded_at
        now = ts
        response = {"message": "Reading ingested"}

        # 1. Glucose threshold (LOW / CRITICAL LOW / HIGH / CRITICAL HIGH)
        threshold_state = validation_service.check_glucose_threshold(payload)
        response["threshold"] = threshold_state.value
        await self._maybe_fire(pid, "glucose", threshold_state, now,
                               GlucoseAlert(pid, str(ts), threshold_state), response, "alert_glucose")

        # 2. Glucose trend (RAPID_DROP / RAPID_RISE / GLUCOSE_SPIKE / GLUCOSE_DROP)
        trend_state = validation_service.check_glucose_trend(payload)
        await self._maybe_fire(pid, "trend", trend_state, now,
                               GlucoseAlert(pid, str(ts), trend_state), response, "alert_trend")

        # 3. Sustained glucose condition (PERSISTENT_HYPOGLYCEMIA / PERSISTENT_HYPERGLYCEMIA)
        sustained_state = validation_service.check_sustained_glucose(payload)
        await self._maybe_fire(pid, "sustained", sustained_state, now,
                               GlucoseAlert(pid, str(ts), sustained_state), response, "alert_sustained")

        # 4. Battery (LOW_BATTERY / CRITICAL_BATTERY)
        battery_state = validation_service.check_battery_level(payload)
        await self._maybe_fire(pid, "battery", battery_state, now,
                               BatteryAlert(pid, str(ts), payload.reading.battery_pct, battery_state),
                               response, "alert_battery")

        # 5. Device health (SENSOR_DEGRADED / DEVICE_OFFLINE)
        health_state = validation_service.check_device_health(payload)
        await self._maybe_fire(pid, "device_health", health_state, now,
                               DeviceHealthAlert(pid, str(ts), health_state), response, "alert_device")

        return validation_status, response


ingestion_service = IngestionService()
