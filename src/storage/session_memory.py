import asyncio
from collections import deque

from src.models.devices import CommunicationDevice, Computer, Mobile
from src.models.enums import StaffType
from src.config import MAX_QUEUE_SIZE, MAX_SEEN_LATE_READINGS
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
        self._alerts: dict[str, deque] = {}
        self._device_map: dict[str, set[CommunicationDevice]] = {}
        # (patient_id, device_id, recorded_at) → prevents duplicate late-reading alerts
        self._seen_late_readings: set[tuple] = set()
        self._lock = asyncio.Lock()

    def get_device(self, patient_id: str) -> set[CommunicationDevice]:
        return self._device_map.get(patient_id, _default_admin_device)

    async def add_alert(self, patient_id: str, alert):
        async with self._lock:
            if patient_id not in self._alerts:
                self._alerts[patient_id] = deque(maxlen=MAX_QUEUE_SIZE)
            self._alerts[patient_id].append(alert)

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
            if len(self._seen_late_readings) >= MAX_SEEN_LATE_READINGS:
                self._seen_late_readings.pop()
            self._seen_late_readings.add(key)
            return False


session_memory = SessionMemory()
