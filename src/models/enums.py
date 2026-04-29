
from enum import Enum

class IngestionStatus(Enum):
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    ERROR = "error"

class ThresholdStatus(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    UNKNOWN = "unknown"
