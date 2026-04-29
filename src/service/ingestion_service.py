from src.models import payload
from src.models.enums import IngestionStatus, ThresholdStatus
from src.service import validation
from src.service.storage_service import StorageService
from src.service.alert import Alert, ThresholdAlert, ValidationAlert
from src.storage.session_memory import session_memory


class IngestionService:

    def _dispatch_alert(self, alert: Alert):
        session_memory.add_alert(alert.patient_id, alert)
        alert.send_alert()

    def process(self, payload: payload.READING_WRAPPER):
        validation_status, validation_message = validation.validate_post_payload(payload)

        if validation_status != IngestionStatus.SUCCESS:
            self._dispatch_alert(ValidationAlert(payload.patient_id, str(payload.reading.recorded_at), validation_message))
            return validation_status, {"message": validation_message}

        StorageService().save_reading(payload)

        threshold_status = validation.check_thresholds(payload)
        if threshold_status != ThresholdStatus.NORMAL:
            self._dispatch_alert(ThresholdAlert(payload.patient_id, str(payload.reading.recorded_at), threshold_status))

        return validation_status, {"message": validation_message}
