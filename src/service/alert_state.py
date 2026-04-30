from datetime import datetime, timedelta
from src.models.enums import AlertType
from src.config import ALERT_COOLDOWN_MINUTES

# Higher number = more severe within a category
_SEVERITY: dict[AlertType, int] = {
    AlertType.NORMAL: 0,
    AlertType.LOW_GLUCOSE: 1,
    AlertType.CRITICAL_LOW_GLUCOSE: 2,
    AlertType.HIGH_GLUCOSE: 1,
    AlertType.CRITICAL_HIGH_GLUCOSE: 2,
    AlertType.GLUCOSE_SPIKE: 1,
    AlertType.GLUCOSE_DROP: 1,
    AlertType.RAPID_RISE: 1,
    AlertType.RAPID_DROP: 1,
    AlertType.PERSISTENT_HYPOGLYCEMIA: 1,
    AlertType.PERSISTENT_HYPERGLYCEMIA: 1,
    AlertType.LOW_BATTERY: 1,
    AlertType.CRITICAL_BATTERY: 2,
    AlertType.SENSOR_DEGRADED: 1,
    AlertType.DEVICE_OFFLINE: 2,
}


class _StateEntry:
    def __init__(self):
        self.state: AlertType = AlertType.NORMAL
        self.fired_at: datetime | None = None


class AlertStateTracker:
    """
      - NORMAL to non-NORMAL: fire alert
      - same state: suppress (regardless of cooldown)
      - lower/different state to higher severity: fire (escalation)
      - any state to NORMAL: update silently (no recovery alert)
      - Cooldown acts as a secondary guard against edge-case re-fires
        for the same state after a long time.
    """

    def __init__(self):
        self._states: dict[str, dict[str, _StateEntry]] = {}

    def _entry(self, patient_id: str, category: str) -> _StateEntry:
        if patient_id not in self._states:
            self._states[patient_id] = {}
        if category not in self._states[patient_id]:
            self._states[patient_id][category] = _StateEntry()
        return self._states[patient_id][category]

    def should_fire(self, patient_id: str, category: str, new_state: AlertType, now: datetime) -> bool:
        if new_state == AlertType.NORMAL:
            return False
        entry = self._entry(patient_id, category)
        if new_state == entry.state:
            return False
        new_sev = _SEVERITY.get(new_state, 0)
        cur_sev = _SEVERITY.get(entry.state, 0)
        if entry.state != AlertType.NORMAL and new_sev <= cur_sev:
            if entry.fired_at and (now - entry.fired_at) < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return False
        return True

    def record_fired(self, patient_id: str, category: str, new_state: AlertType, now: datetime):
        entry = self._entry(patient_id, category)
        entry.state = new_state
        entry.fired_at = now

    def update_state(self, patient_id: str, category: str, new_state: AlertType):
        self._entry(patient_id, category).state = new_state

    def get_state(self, patient_id: str, category: str) -> AlertType:
        return self._entry(patient_id, category).state


alert_state_tracker = AlertStateTracker()
