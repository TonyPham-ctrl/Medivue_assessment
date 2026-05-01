import contextlib
import sqlite3
from datetime import datetime, timedelta, timezone
from src.models.enums import AlertType
from src.config import ALERT_COOLDOWN_MINUTES, DB_PATH, DB_ALERT_STATE_TABLE

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
    AlertType.LATE_READING: 1,
}


def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class AlertStateTracker:
    """
      - NORMAL to non-NORMAL: fire alert
      - same state: suppress (regardless of cooldown)
      - lower/different state to higher severity: fire (escalation)
      - any state to NORMAL: update silently (no recovery alert)
      - Cooldown acts as a secondary guard against edge-case re-fires
        for the same state after a long time.

    State is persisted to SQLite so it survives server restarts.
    device_id defaults to '' for patient-level categories; pass the
    actual device_id for device-level categories (e.g. 'late_reading').
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _read(self, patient_id: str, device_id: str, category: str) -> tuple[AlertType, datetime | None]:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT state, fired_at FROM {DB_ALERT_STATE_TABLE} "
                "WHERE patient_id=? AND device_id=? AND category=?",
                (patient_id, device_id, category),
            )
            row = cursor.fetchone()
        if row is None:
            return AlertType.NORMAL, None
        try:
            state = AlertType(row[0])
        except ValueError:
            state = AlertType.NORMAL
        fired_at = datetime.fromisoformat(row[1]) if row[1] else None
        return state, fired_at

    def _upsert(
        self,
        patient_id: str,
        device_id: str,
        category: str,
        state: AlertType,
        fired_at: datetime | None,
        update_fired_at: bool,
    ):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                if update_fired_at:
                    conn.execute(
                        f"INSERT INTO {DB_ALERT_STATE_TABLE} "
                        "(patient_id, device_id, category, state, fired_at) "
                        "VALUES (?, ?, ?, ?, ?) "
                        "ON CONFLICT(patient_id, device_id, category) "
                        "DO UPDATE SET state=excluded.state, fired_at=excluded.fired_at",
                        (
                            patient_id, device_id, category, state.value,
                            fired_at.isoformat() if fired_at else None,
                        ),
                    )
                else:
                    conn.execute(
                        f"INSERT INTO {DB_ALERT_STATE_TABLE} "
                        "(patient_id, device_id, category, state, fired_at) "
                        "VALUES (?, ?, ?, ?, NULL) "
                        "ON CONFLICT(patient_id, device_id, category) "
                        "DO UPDATE SET state=excluded.state",
                        (patient_id, device_id, category, state.value),
                    )

    def should_fire(
        self,
        patient_id: str,
        category: str,
        new_state: AlertType,
        now: datetime,
        device_id: str = "",
    ) -> bool:
        if new_state == AlertType.NORMAL:
            return False
        cur_state, fired_at = self._read(patient_id, device_id, category)
        if new_state == cur_state:
            return False
        new_sev = _SEVERITY.get(new_state, 0)
        cur_sev = _SEVERITY.get(cur_state, 0)
        if cur_state != AlertType.NORMAL and new_sev <= cur_sev:
            if fired_at and (_naive_utc(now) - fired_at) < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return False
        return True

    def record_fired(
        self,
        patient_id: str,
        category: str,
        new_state: AlertType,
        now: datetime,
        device_id: str = "",
    ):
        self._upsert(patient_id, device_id, category, new_state, _naive_utc(now), update_fired_at=True)

    def update_state(
        self,
        patient_id: str,
        category: str,
        new_state: AlertType,
        device_id: str = "",
    ):
        self._upsert(patient_id, device_id, category, new_state, None, update_fired_at=False)

    def get_state(self, patient_id: str, category: str, device_id: str = "") -> AlertType:
        state, _ = self._read(patient_id, device_id, category)
        return state


alert_state_tracker = AlertStateTracker()
