from src.models import payload
from src.service import validation
from src.service.storage_service import StorageService

class IngestionService:
    def process(self, payload: payload.ReadingWrapper):
        status_code, message = validation.validate_post_payload(payload)

        if status_code == 200:
            StorageService().save_reading(payload)

        return status_code, {"message": message}
    




