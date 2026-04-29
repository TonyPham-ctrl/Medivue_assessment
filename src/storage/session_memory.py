from src.config import MAX_SESSION_SIZE
from src.models.devices import CommunicationDevice, Computer, Mobile
from src.models.enums import StaffType

_default_admin_device = {Computer(
    device_id="admin-console",
    owner=StaffType.ADMIN,
    contact_info="admin@medivue.local"
), Mobile(
    device_id="admin-mobile",
    owner=StaffType.ADMIN,
    contact_info="+1-555-0000"
)
}

# Boilerplate: extend these to map specific patients to doctors/nurses
# _doctor_device = Mobile(device_id="dr-mobile", owner=StaffType.DOCTOR, contact_info="+1-555-0100")
# _nurse_device  = Mobile(device_id="nurse-mobile", owner=StaffType.NURSE, contact_info="+1-555-0101")

class SessionMemory:
    def __init__(self):
        self._readings: dict[str, list] = {}
        self._alerts: dict[str, list] = {}
        self._device_map: dict[str, set[CommunicationDevice]] = {}
        self.max_size = MAX_SESSION_SIZE

    def get_device(self, patient_id: str) -> set[CommunicationDevice]:
        return self._device_map.get(patient_id, _default_admin_device)

    def register_device(self, patient_id: str, device: CommunicationDevice):
        if patient_id not in self._device_map:
            self._device_map[patient_id] = set()
        self._device_map[patient_id].add(device)

    def add_reading(self, patient_id: str, reading):
        if patient_id not in self._readings:
            self._readings[patient_id] = []
        session = self._readings[patient_id]
        session.append(reading)
        if len(session) > self.max_size:
            session.pop(0)

    def get_readings(self, patient_id: str) -> list:
        return self._readings.get(patient_id, [])

    def add_alert(self, patient_id: str, alert):
        if patient_id not in self._alerts:
            self._alerts[patient_id] = []
        self._alerts[patient_id].append(alert)

    def get_alerts(self, patient_id: str) -> list:
        return self._alerts.get(patient_id, [])


session_memory = SessionMemory()
