from abc import ABC, abstractmethod
from datetime import datetime
from src.models.enums import AlertType
from src.storage.session_memory import session_memory

_ALERT_MESSAGES = {
    AlertType.LOW_GLUCOSE:               "glucose is low (< 70 mg/dL)",
    AlertType.CRITICAL_LOW_GLUCOSE:      "glucose is critically low (< 54 mg/dL)",
    AlertType.HIGH_GLUCOSE:              "glucose is high (> 180 mg/dL)",
    AlertType.CRITICAL_HIGH_GLUCOSE:     "glucose is critically high (> 250 mg/dL)",
    AlertType.UNKNOWN_GLUCOSE:           "no glucose threshold configured for this patient",
    AlertType.GLUCOSE_SPIKE:             "statistical glucose spike detected",
    AlertType.GLUCOSE_DROP:              "statistical glucose drop detected",
    AlertType.RAPID_RISE:                "rapid glucose rise (> 50 mg/dL in 30 min)",
    AlertType.RAPID_DROP:                "rapid glucose drop (> 30 mg/dL in 15 min)",
    AlertType.PERSISTENT_HYPOGLYCEMIA:   "persistent hypoglycemia (low glucose sustained > 15 min)",
    AlertType.PERSISTENT_HYPERGLYCEMIA:  "persistent hyperglycemia (high glucose sustained > 30 min)",
    AlertType.LOW_BATTERY:               "device battery low (< 20%)",
    AlertType.CRITICAL_BATTERY:          "device battery critical (< 10%)",
    AlertType.SENSOR_DEGRADED:           "sensor signal degraded over consecutive readings",
    AlertType.DEVICE_OFFLINE:            "device was offline — gap detected in readings",
}


class Alert(ABC):
    def __init__(self, patient_id: str, recorded_at: str):
        self.patient_id = patient_id
        self.recorded_at = recorded_at

    @abstractmethod
    def _build_message(self) -> str: ...

    def send_alert(self) -> str:
        message = self._build_message()
        for device in session_memory.get_device(self.patient_id):
            device.contact(message)
        return message


class GlucoseAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, alert_type: AlertType):
        super().__init__(patient_id, recorded_at)
        self.alert_type = alert_type

    def _build_message(self) -> str:
        description = _ALERT_MESSAGES.get(self.alert_type, self.alert_type.value)
        return f"[{self.alert_type.value}] Patient {self.patient_id} — {description} at {self.recorded_at}"


class ValidationAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, validation_message: str):
        super().__init__(patient_id, recorded_at)
        self.validation_message = validation_message

    def _build_message(self) -> str:
        return f"[invalid] Patient {self.patient_id} — invalid reading at {self.recorded_at}: {self.validation_message}"


class BatteryAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, battery_pct: int, alert_type: AlertType):
        super().__init__(patient_id, recorded_at)
        self.battery_pct = battery_pct
        self.alert_type = alert_type

    def _build_message(self) -> str:
        description = _ALERT_MESSAGES.get(self.alert_type, self.alert_type.value)
        return f"[{self.alert_type.value}] Patient {self.patient_id} — {description} ({self.battery_pct}%) at {self.recorded_at}"


class DeviceHealthAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, alert_type: AlertType):
        super().__init__(patient_id, recorded_at)
        self.alert_type = alert_type

    def _build_message(self) -> str:
        description = _ALERT_MESSAGES.get(self.alert_type, self.alert_type.value)
        return f"[{self.alert_type.value}] Patient {self.patient_id} — {description} at {self.recorded_at}"


class LateReadingAlert(Alert):
    def __init__(
        self,
        patient_id: str,
        device_id: str,
        recorded_at: datetime,
        arrival_time: datetime,
        lateness_minutes: int,
    ):
        super().__init__(patient_id, str(recorded_at))
        self.device_id = device_id
        self.arrival_time = arrival_time
        self.lateness_minutes = lateness_minutes

    def _build_message(self) -> str:
        return (
            f"[LATE_READING] Patient {self.patient_id} device {self.device_id} — "
            f"reading arrived {self.lateness_minutes} min late (recorded {self.recorded_at})"
        )

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "device_id": self.device_id,
            "type": "LATE_READING",
            "severity": "WARNING",
            "event_time": self.recorded_at,
            "arrival_time": str(self.arrival_time),
            "lateness_minutes": self.lateness_minutes,
        }
