from src.models.payload import ReadingWrapper
from src.models.enums import IngestionStatus, AlertType
from src.service.validation import validation_service
from src.service.storage_service import storage_service
from src.service.alert import Alert, GlucoseAlert, ValidationAlert
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

        alert_type = validation_service.check_thresholds(payload)
        if alert_type != AlertType.NORMAL:
            alert_message = self._dispatch_alert(GlucoseAlert(payload.patient_id, str(payload.reading.recorded_at), alert_type))
            return validation_status, {"message": "Reading ingested", "threshold": alert_type.value, "alert": alert_message}

        return validation_status, {"message": "Reading ingested", "threshold": alert_type.value}
