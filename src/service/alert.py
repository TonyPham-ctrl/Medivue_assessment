from abc import ABC, abstractmethod
from src.models.enums import AlertType
from src.storage.session_memory import session_memory

_ALERT_MESSAGES = {
    AlertType.LOW_GLUCOSE:      "glucose is critically low",
    AlertType.HIGH_GLUCOSE:     "glucose is critically high",
    AlertType.UNKNOWN_GLUCOSE:  "no glucose threshold configured for this patient",
    AlertType.GLUCOSE_SPIKE:    "rapid glucose spike detected",
    AlertType.GLUCOSE_DROP:     "rapid glucose drop detected",
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

    def _get_alert_type(self) -> str:
        return self.alert_type.value


class ValidationAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, validation_message: str):
        super().__init__(patient_id, recorded_at)
        self.validation_message = validation_message

    def _build_message(self) -> str:
        return f"[invalid] Patient {self.patient_id} — invalid reading at {self.recorded_at}: {self.validation_message}"


class BatteryAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, battery_pct: int):
        super().__init__(patient_id, recorded_at)
        self.battery_pct = battery_pct

    def _build_message(self) -> str:
        return f"[low_battery] Patient {self.patient_id} — device battery at {self.battery_pct}% at {self.recorded_at}"
