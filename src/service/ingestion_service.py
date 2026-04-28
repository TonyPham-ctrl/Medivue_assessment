from src.models import payload
from src.utils import validate_post_payload


def process(payload: payload.ReadingWrapper):
    is_valid, message = validate_post_payload(payload)

    if not is_valid:
        raise ValueError(message)
    
    



