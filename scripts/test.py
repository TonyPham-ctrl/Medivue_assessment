import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from src.models.payload import ReadingWrapper, ReadingPayload
from src.models.enums import IngestionStatus, AlertType
from src.service.ingestion_service import IngestionService
from src.storage.sqlite_db import init_readings_table, init_patient_glucose_table
from src.config import DB_READING_PATH, DB_PATIENT_GLUCOSE_PATH
from scripts.seed import seed


def make_payload(device_id, patient_id, glucose, battery, signal, recorded_at):
    return ReadingWrapper(
        device_id=device_id,
        patient_id=patient_id,
        reading=ReadingPayload(
            glucose_mgdl=glucose,
            battery_pct=battery,
            signal_quality=signal,
            recorded_at=recorded_at,
        )
    )

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

results = []

def run_test(name, payload, expect_status, expect_threshold=None, expect_alert=True):
    print(f"\n{'─'*60}")
    print(f"TEST: {name}")
    print(f"{'─'*60}")
    try:
        status, response = IngestionService().process(payload)
        print(f"  status   : {status}")
        print(f"  response : {response}")

        ok = status == expect_status
        if expect_threshold is not None:
            ok = ok and response.get("threshold") == expect_threshold.value
        if expect_alert:
            ok = ok and "alert" in response

        label = PASS if ok else FAIL
        print(f"  result   : {label}")
        results.append((name, ok))
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append((name, False))


print("=" * 60)
print("STEP 1 — clearing database")
print("=" * 60)
for path in [DB_READING_PATH, DB_PATIENT_GLUCOSE_PATH]:
    if os.path.exists(path):
        os.remove(path)
        print(f"  deleted {path}")
init_readings_table()
init_patient_glucose_table()

print("\n" + "=" * 60)
print("STEP 2 — seeding fake data")
print("=" * 60)
seed()


print("\n" + "=" * 60)
print("STEP 3 — running test cases")
print("=" * 60)


run_test(
    "Normal glucose (within bounds)",
    make_payload("dev-a", "p001", 105.0, 90, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    expect_alert=False,
)
run_test(
    "High glucose (above upper bound)",
    make_payload("dev-a", "p001", 180.0, 85, "good", datetime(2026, 5, 1, 9, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.HIGH_GLUCOSE,
    expect_alert=True,
)

run_test(
    "Low glucose (below lower bound)",
    make_payload("dev-b", "p002", 50.0, 80, "good", datetime(2026, 5, 1, 10, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_alert=True,
)

run_test(
    "Duplicate reading (same device + timestamp)",
    make_payload("dev-a", "p001", 100.0, 85, "good", datetime(2026, 4, 30, 8, 0, 0)),
    expect_status=IngestionStatus.DUPLICATE,
    expect_alert=True,
)

run_test(
    "Invalid: empty device_id",
    make_payload("", "p001", 100.0, 85, "good", datetime(2026, 5, 1, 11, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_alert=True,
)

run_test(
    "Invalid: glucose = 0 (boundary edge)",
    make_payload("dev-a", "p001", 0.0, 85, "good", datetime(2026, 5, 1, 12, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_alert=True,
)

run_test(
    "Invalid: battery_pct = 101",
    make_payload("dev-a", "p001", 100.0, 101, "good", datetime(2026, 5, 1, 13, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_alert=True,
)

run_test(
    "Invalid: signal_quality = 'excellent'",
    make_payload("dev-a", "p001", 100.0, 85, "excellent", datetime(2026, 5, 1, 14, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_alert=True,
)

run_test(
    "Unknown patient (no threshold configured)",
    make_payload("dev-z", "p999", 100.0, 85, "good", datetime(2026, 5, 1, 15, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.UNKNOWN_GLUCOSE,
    expect_alert=True,
)

run_test(
    "Glucose exactly at upper bound (140.0) — expect NORMAL",
    make_payload("dev-a", "p001", 140.0, 85, "good", datetime(2026, 5, 1, 16, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    expect_alert=False,
)


print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    label = PASS if ok else FAIL
    print(f"  [{label}] {name}")
print(f"\n  {passed}/{len(results)} passed")
