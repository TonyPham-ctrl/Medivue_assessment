from abc import ABC, abstractmethod
from src.models.enums import ThresholdStatus
from src.storage.session_memory import session_memory


class Alert(ABC):
    def __init__(self, patient_id: str, recorded_at: str):
        self.patient_id = patient_id
        self.recorded_at = recorded_at

    @abstractmethod
    def _build_message(self) -> str: ...

    def send_alert(self):
        devices = session_memory.get_device(self.patient_id)
        message = self._build_message()
        for device in devices:
            device.contact(message)


class ThresholdAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, threshold_status: ThresholdStatus):
        super().__init__(patient_id, recorded_at)
        self.threshold_status = threshold_status

    def _build_message(self) -> str:
        return f"Patient {self.patient_id} glucose is {self.threshold_status.value} at {self.recorded_at}"


class ValidationAlert(Alert):
    def __init__(self, patient_id: str, recorded_at: str, validation_message: str):
        super().__init__(patient_id, recorded_at)
        self.validation_message = validation_message

    def _build_message(self) -> str:
        return f"Invalid reading from patient {self.patient_id} at {self.recorded_at}: {self.validation_message}"
