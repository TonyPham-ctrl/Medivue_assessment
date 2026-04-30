
from enum import Enum

class IngestionStatus(Enum):
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    ERROR = "error"

class AlertType(Enum):
    NORMAL = "normal"
    LOW_GLUCOSE = "low_glucose"
    CRITICAL_LOW_GLUCOSE = "critical_low_glucose"
    HIGH_GLUCOSE = "high_glucose"
    CRITICAL_HIGH_GLUCOSE = "critical_high_glucose"
    UNKNOWN_GLUCOSE = "unknown_glucose"

    GLUCOSE_SPIKE = "glucose_spike"
    GLUCOSE_DROP = "glucose_drop"
    RAPID_RISE = "rapid_rise"
    RAPID_DROP = "rapid_drop"

    PERSISTENT_HYPOGLYCEMIA = "persistent_hypoglycemia"
    PERSISTENT_HYPERGLYCEMIA = "persistent_hyperglycemia"

    LOW_BATTERY = "low_battery"
    CRITICAL_BATTERY = "critical_battery"

    SENSOR_DEGRADED = "sensor_degraded"
    DEVICE_OFFLINE = "device_offline"

    LATE_READING = "late_reading"

class StaffType(Enum):
    NURSE = "nurse"
    DOCTOR = "doctor"
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"