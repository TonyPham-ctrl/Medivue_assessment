import asyncio

from src.models.devices import CommunicationDevice, Computer, Mobile
from src.models.enums import StaffType

_default_admin_device = [
    Computer(
        device_id="admin-console",
        owner=StaffType.ADMIN,
        contact_info="admin@medivue.local"
    ),
    Mobile(
        device_id="admin-mobile",
        owner=StaffType.ADMIN,
        contact_info="+1-555-0000"
    )
]

# Boilerplate: extend these to map specific patients to doctors/nurses
# _doctor_device = Mobile(device_id="dr-mobile", owner=StaffType.DOCTOR, contact_info="+1-555-0100")
# _nurse_device  = Mobile(device_id="nurse-mobile", owner=StaffType.NURSE, contact_info="+1-555-0101")

class SessionMemory:
    def __init__(self):
        self._alerts: dict[str, list] = {}
        self._device_map: dict[str, set[CommunicationDevice]] = {}
        self._lock = asyncio.Lock()

    def get_device(self, patient_id: str) -> set[CommunicationDevice]:
        return self._device_map.get(patient_id, _default_admin_device)

    async def add_alert(self, patient_id: str, alert):
        async with self._lock:
            if patient_id not in self._alerts:
                self._alerts[patient_id] = []
            self._alerts[patient_id].append(alert)

    def get_alerts(self, patient_id: str):
        return self._alerts.get(patient_id, [])

session_memory = SessionMemory()
