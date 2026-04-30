import asyncio
from queue import Queue

from src.models.devices import CommunicationDevice, Computer, Mobile
from src.models.enums import StaffType
from src.config import MAX_QUEUE_SIZE
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
        self._alerts: dict[str, Queue] = {}
        self._device_map: dict[str, set[CommunicationDevice]] = {}
        # (patient_id, device_id, recorded_at) → prevents duplicate late-reading alerts
        self._seen_late_readings: set[tuple] = set()
        # (patient_id, device_id) → "ACTIVE" | "RESOLVED"
        self._late_alert_state: dict[tuple, str] = {}
        self._lock = asyncio.Lock()

    def get_device(self, patient_id: str) -> set[CommunicationDevice]:
        return self._device_map.get(patient_id, _default_admin_device)

    async def add_alert(self, patient_id: str, alert):
        async with self._lock:
            if patient_id not in self._alerts:
                self._alerts[patient_id] = Queue()
            self._alerts[patient_id].put(alert)
            if self._alerts[patient_id].qsize() > MAX_QUEUE_SIZE:
                self._alerts[patient_id].get()

    def get_alerts(self, patient_id: str):
        return self._alerts.get(patient_id, [])

    async def check_and_mark_late_seen(
        self, patient_id: str, device_id: str, recorded_at
    ) -> bool:
        """Atomically checks and marks a reading for late-detection processing.
        Returns True if already seen (caller should skip), False if newly registered."""
        key = (patient_id, device_id, recorded_at)
        async with self._lock:
            if key in self._seen_late_readings:
                return True
            self._seen_late_readings.add(key)
            return False

    def get_late_alert_state(self, patient_id: str, device_id: str) -> str | None:
        return self._late_alert_state.get((patient_id, device_id))

    async def set_late_alert_state(self, patient_id: str, device_id: str, state: str):
        async with self._lock:
            self._late_alert_state[(patient_id, device_id)] = state

session_memory = SessionMemory()
