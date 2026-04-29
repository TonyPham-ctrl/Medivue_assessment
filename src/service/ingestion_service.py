from src.models.payload import ReadingWrapper
from src.models.enums import IngestionStatus, AlertType
from src.service.validation import validation_service
from src.service.storage_service import storage_service
from src.service.alert import Alert, GlucoseAlert, ValidationAlert, BatteryAlert
from src.storage.session_memory import session_memory


class IngestionService:

    def _dispatch_alert(self, alert: Alert) -> str:
        session_memory.add_alert(alert.patient_id, alert)
        return alert.send_alert()

    def process(self, payload: ReadingWrapper):
        validation_status, validation_message = validation_service.validate_post_payload(payload)

        if validation_status != IngestionStatus.SUCCESS:
            alert_message = self._dispatch_alert(ValidationAlert(payload.patient_id, str(payload.reading.recorded_at), validation_message))
            return validation_status, {"message": validation_message, "alert": alert_message}

        storage_service.save_reading(payload)

        response = {"message": "Reading ingested"}

        alert_type = validation_service.check_thresholds(payload)
        if alert_type != AlertType.NORMAL:
            response["threshold"] = alert_type.value
            response["alert"] = self._dispatch_alert(GlucoseAlert(payload.patient_id, str(payload.reading.recorded_at), alert_type))
        else:
            response["threshold"] = alert_type.value

        if validation_service.check_battery(payload):
            response["battery_alert"] = self._dispatch_alert(BatteryAlert(payload.patient_id, str(payload.reading.recorded_at), payload.reading.battery_pct))

        return validation_status, response
