from src.models import payload
from src.service import validation
from src.service import StorageService

def process(payload: payload.ReadingWrapper):
    status_code, message = validation.validate_post_payload(payload)

    if status_code == 200:
        StorageService().save_reading(payload)
        return {"message": "Reading ingested successfully"}
    else:
        raise ValueError(message)
    




