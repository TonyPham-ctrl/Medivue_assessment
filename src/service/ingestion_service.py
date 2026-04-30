from datetime import datetime, timezone
from typing import Optional
from src.models.payload import ReadingWrapper
from src.models.enums import IngestionStatus, AlertType
from src.service.validation import validation_service
from src.service.storage_service import storage_service
from src.service.alert import Alert, GlucoseAlert, ValidationAlert, BatteryAlert, DeviceHealthAlert, LateReadingAlert
from src.service.alert_state import alert_state_tracker
from src.storage.session_memory import session_memory
from src.config import LATE_READING_THRESHOLD_MINUTES


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

    async def process_reading(
        self, reading: ReadingWrapper, arrival_time: datetime
    ) -> Optional[dict]:
        """Detects late readings and returns an alert dict if a new alert was fired.

        Correctness guarantees:
        - Lateness is always computed from timestamps (arrival_time - recorded_at),
          never inferred from arrival order.
        - Idempotent: the same (patient_id, device_id, recorded_at) triple is only
          processed once per session.
        - State-based: only one ACTIVE late-reading alert is maintained per device;
          repeat late readings suppress new alerts until the device recovers.
        """
        pid = reading.patient_id
        did = reading.device_id
        recorded_at = reading.reading.recorded_at

        # Idempotency guard — atomic check-and-mark
        if await session_memory.check_and_mark_late_seen(pid, did, recorded_at):
            return None

        # Normalise both timestamps to naive UTC so subtraction always works
        # regardless of whether the client sends tz-aware or tz-naive datetimes.
        def _naive_utc(dt: datetime) -> datetime:
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        lateness_seconds = (_naive_utc(arrival_time) - _naive_utc(recorded_at)).total_seconds()

        if lateness_seconds <= LATE_READING_THRESHOLD_MINUTES * 60:
            # On-time reading — resolve any prior active late alert for this device
            if session_memory.get_late_alert_state(pid, did) == "ACTIVE":
                await session_memory.set_late_alert_state(pid, did, "RESOLVED")
            return None

        lateness_minutes = int(lateness_seconds / 60)

        # Suppress if an ACTIVE alert already exists for this device
        if session_memory.get_late_alert_state(pid, did) == "ACTIVE":
            return None

        alert = LateReadingAlert(pid, did, recorded_at, arrival_time, lateness_minutes)
        await session_memory.set_late_alert_state(pid, did, "ACTIVE")
        await self._dispatch_alert(alert)
        return alert.to_dict()

    async def process(self, payload: ReadingWrapper, arrival_time: datetime):
        validation_status, validation_message = validation_service.validate_post_payload(payload)

        if validation_status == IngestionStatus.DUPLICATE:
            return validation_status, {"message": validation_message}

        if validation_status != IngestionStatus.SUCCESS:
            alert_message = await self._dispatch_alert(
                ValidationAlert(payload.patient_id, payload.reading.recorded_at, validation_message)
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
                               GlucoseAlert(pid, ts, threshold_state), response, "alert_glucose")

        # 2. Glucose trend (RAPID_DROP / RAPID_RISE / GLUCOSE_SPIKE / GLUCOSE_DROP)
        trend_state = validation_service.check_glucose_trend(payload)
        await self._maybe_fire(pid, "trend", trend_state, now,
                               GlucoseAlert(pid, ts, trend_state), response, "alert_trend")

        # 3. Sustained glucose condition (PERSISTENT_HYPOGLYCEMIA / PERSISTENT_HYPERGLYCEMIA)
        sustained_state = validation_service.check_sustained_glucose(payload)
        await self._maybe_fire(pid, "sustained", sustained_state, now,
                               GlucoseAlert(pid, ts, sustained_state), response, "alert_sustained")

        # 4. Battery (LOW_BATTERY / CRITICAL_BATTERY)
        battery_state = validation_service.check_battery_level(payload)
        await self._maybe_fire(pid, "battery", battery_state, now,
                               BatteryAlert(pid, ts, payload.reading.battery_pct, battery_state),
                               response, "alert_battery")

        # 5. Device health (SENSOR_DEGRADED / DEVICE_OFFLINE)
        health_state = validation_service.check_device_health(payload)
        await self._maybe_fire(pid, "device_health", health_state, now,
                               DeviceHealthAlert(pid, ts, health_state), response, "alert_device")

        # 6. Late reading (event-time vs arrival-time, state-based, idempotent)
        late_alert = await self.process_reading(payload, arrival_time)
        if late_alert:
            response["alert_late_reading"] = late_alert

        return validation_status, response


ingestion_service = IngestionService()
