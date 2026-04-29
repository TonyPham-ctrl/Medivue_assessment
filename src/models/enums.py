
from enum import Enum

class IngestionStatus(Enum):
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    ERROR = "error"

class AlertType(Enum):
    NORMAL = "normal"
    LOW_GLUCOSE = "low_glucose"
    HIGH_GLUCOSE = "high_glucose"
    UNKNOWN_GLUCOSE = "unknown_glucose"
    GLUCOSE_SPIKE = "glucose_spike"
    GLUCOSE_DROP = "glucose_drop"

class StaffType(Enum):
    NURSE = "nurse"
    DOCTOR = "doctor"
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"