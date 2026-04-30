
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from src.storage.sqlite_db import init_db
from src.service.storage_service import StorageService
from src.service.patient_glucose_service import PatientGlucoseService

THRESHOLDS = [
    {"patient_id": "p001", "lower_bound": 70.0,  "upper_bound": 140.0},
    {"patient_id": "p002", "lower_bound": 80.0,  "upper_bound": 160.0},
    {"patient_id": "p003", "lower_bound": 60.0,  "upper_bound": 120.0},
    {"patient_id": "p004", "lower_bound": 70.0,  "upper_bound": 200.0},
]


READINGS = [
    # p001 — normal
    {"device_id": "dev-a", "patient_id": "p001", "glucose_mgdl": 100.0, "battery_pct": 85, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 8,  0, 0)},
    # p001 — high
    {"device_id": "dev-a", "patient_id": "p001", "glucose_mgdl": 200.0, "battery_pct": 80, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 9,  0, 0)},
    # p002 — normal
    {"device_id": "dev-b", "patient_id": "p002", "glucose_mgdl": 120.0, "battery_pct": 90, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 8, 30, 0)},
    # p002 — low
    {"device_id": "dev-b", "patient_id": "p002", "glucose_mgdl": 55.0,  "battery_pct": 88, "signal_quality": "poor",      "recorded_at": datetime(2026, 4, 30, 10, 0, 0)},
    # p003 — normal
    {"device_id": "dev-c", "patient_id": "p003", "glucose_mgdl": 95.0,  "battery_pct": 75, "signal_quality": "degraded",  "recorded_at": datetime(2026, 4, 30, 7, 45, 0)},
    # p004 — tightly clustered baseline for stat anomaly testing
    {"device_id": "dev-d", "patient_id": "p004", "glucose_mgdl": 100.0, "battery_pct": 15, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 8,  0, 0)},
    {"device_id": "dev-d", "patient_id": "p004", "glucose_mgdl": 101.0, "battery_pct": 15, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 9,  0, 0)},
    {"device_id": "dev-d", "patient_id": "p004", "glucose_mgdl":  99.0, "battery_pct": 15, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 10, 0, 0)},
    {"device_id": "dev-d", "patient_id": "p004", "glucose_mgdl": 100.0, "battery_pct": 15, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 11, 0, 0)},
    {"device_id": "dev-d", "patient_id": "p004", "glucose_mgdl": 102.0, "battery_pct": 15, "signal_quality": "good",      "recorded_at": datetime(2026, 4, 30, 12, 0, 0)},

    {"device_id": "dev-rdrop",        "patient_id": "p-rdrop",        "glucose_mgdl": 200.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1,  8,  0, 0)},
    {"device_id": "dev-rrise",        "patient_id": "p-rrise",        "glucose_mgdl": 100.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1,  9,  0, 0)},
    {"device_id": "dev-persis-hypo",  "patient_id": "p-persis-hypo",  "glucose_mgdl":  65.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1, 10,  0, 0)},
    {"device_id": "dev-persis-hypo",  "patient_id": "p-persis-hypo",  "glucose_mgdl":  67.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1, 10,  5, 0)},
    {"device_id": "dev-persis-hyper", "patient_id": "p-persis-hyper", "glucose_mgdl": 200.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1, 11,  0, 0)},
    {"device_id": "dev-persis-hyper", "patient_id": "p-persis-hyper", "glucose_mgdl": 210.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1, 11, 10, 0)},
    {"device_id": "dev-persis-hyper", "patient_id": "p-persis-hyper", "glucose_mgdl": 195.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1, 11, 20, 0)},
    {"device_id": "dev-sensor",       "patient_id": "p-sensor",       "glucose_mgdl": 100.0, "battery_pct": 80, "signal_quality": "poor",     "recorded_at": datetime(2026, 6, 1, 12,  0, 0)},
    {"device_id": "dev-sensor",       "patient_id": "p-sensor",       "glucose_mgdl": 100.0, "battery_pct": 80, "signal_quality": "degraded", "recorded_at": datetime(2026, 6, 1, 12,  5, 0)},
    {"device_id": "dev-offline",      "patient_id": "p-offline",      "glucose_mgdl": 100.0, "battery_pct": 80, "signal_quality": "good",     "recorded_at": datetime(2026, 6, 1,  7,  0, 0)},
]


class _FakePayload:
    class _Reading:
        def __init__(self, r):
            self.glucose_mgdl  = r["glucose_mgdl"]
            self.battery_pct   = r["battery_pct"]
            self.signal_quality = r["signal_quality"]
            self.recorded_at   = r["recorded_at"]
    def __init__(self, r):
        self.device_id  = r["device_id"]
        self.patient_id = r["patient_id"]
        self.reading    = self._Reading(r)


class _FakeThreshold:
    def __init__(self, t):
        self.patient_id  = t["patient_id"]
        self.lower_bound = t["lower_bound"]
        self.upper_bound = t["upper_bound"]


def seed():
    init_db()

    pg = PatientGlucoseService()
    for t in THRESHOLDS:
        pg.save_patient_glucose(_FakeThreshold(t))
        print(f"  threshold saved — {t['patient_id']}: {t['lower_bound']}–{t['upper_bound']}")

    ss = StorageService()
    for r in READINGS:
        ss.save_reading(_FakePayload(r))
        print(f"  reading saved   — {r['patient_id']} glucose={r['glucose_mgdl']} at {r['recorded_at']}")

    print("Seed complete.")


if __name__ == "__main__":
    seed()
