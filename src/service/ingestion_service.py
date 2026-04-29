from src.models import payload
from src.models.enums import IngestionStatus
from src.service import validation
from src.service.storage_service import StorageService

class IngestionService:

    def handle_validation_result(self, status_code, message, payload):
        if status_code == IngestionStatus.SUCCESS:
            StorageService().save_reading(payload)
            return
        else:
            raise ValueError(message)

    def handle_threshold_status(self, threshold_status, payload):
        if threshold_status in [validation.ThresholdStatus.LOW, validation.ThresholdStatus.HIGH]:
            pass
        elif threshold_status == validation.ThresholdStatus.UNKNOWN:
            pass

        return

    def process(self, payload: payload.READING_WRAPPER):
        validation_status, validation_message = validation.validate_post_payload(payload)
        self.handle_validation_result(validation_status, validation_message, payload)

        threshold_status = validation.check_thresholds(payload)
        self.handle_threshold_status(threshold_status, payload)
        return validation_status, {"message": validation_message, "threshold": threshold_status.value}





