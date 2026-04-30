import sys, os, asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from src.models.payload import ReadingWrapper, ReadingPayload
from src.models.enums import IngestionStatus, AlertType
from src.service.ingestion_service import IngestionService
from src.storage.sqlite_db import init_db
from src.config import DB_PATH
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


def run_test(name, payload, expect_status, expect_threshold=None, expect_keys=None, reject_keys=None):
    """
    expect_threshold : AlertType expected at response["threshold"]
    expect_keys      : response keys that must be present
    reject_keys      : response keys that must NOT be present
    Returns (status, response) for multi-step tests.
    """
    print(f"\n{'─'*60}")
    print(f"TEST: {name}")
    print(f"{'─'*60}")
    try:
        status, response = asyncio.run(IngestionService().process(payload))
        print(f"  status   : {status}")
        print(f"  response : {response}")

        ok = status == expect_status
        if expect_threshold is not None and response.get("threshold") != expect_threshold.value:
            print(f"  ✗ threshold: expected {expect_threshold.value!r}, got {response.get('threshold')!r}")
            ok = False
        for key in (expect_keys or []):
            if key not in response:
                print(f"  ✗ expected key {key!r} not in response")
                ok = False
        for key in (reject_keys or []):
            if key in response:
                print(f"  ✗ unexpected key {key!r} present in response")
                ok = False

        label = PASS if ok else FAIL
        print(f"  result   : {label}")
        results.append((name, ok))
        return status, response
    except Exception as e:
        import traceback; traceback.print_exc()
        results.append((name, False))
        return None, {}


def section(title):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")



print("=" * 60)
print("STEP 1 — clearing database")
print("=" * 60)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"  deleted {DB_PATH}")
init_db()

print("\n" + "=" * 60)
print("STEP 2 — seeding data")
print("=" * 60)
seed()

print("\n" + "=" * 60)
print("STEP 3 — running tests")
print("=" * 60)


section("1 · VALIDATION")

run_test(
    "Invalid: empty device_id",
    make_payload("", "p001", 100.0, 80, "good", datetime(2026, 5, 1, 11, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_keys=["alert"],
)
run_test(
    "Invalid: glucose = 0 (at boundary)",
    make_payload("dev-a", "p001", 0.0, 80, "good", datetime(2026, 5, 1, 12, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_keys=["alert"],
)
run_test(
    "Invalid: signal_quality = 'excellent'",
    make_payload("dev-a", "p001", 100.0, 80, "excellent", datetime(2026, 5, 1, 14, 0, 0)),
    expect_status=IngestionStatus.INVALID,
    expect_keys=["alert"],
)
run_test(
    "Duplicate reading (same device + timestamp as seeded record)",
    make_payload("dev-a", "p001", 100.0, 80, "good", datetime(2026, 4, 30, 8, 0, 0)),
    expect_status=IngestionStatus.DUPLICATE,
    expect_keys=["alert"],
)


section("2 · GLUCOSE THRESHOLD TIERS")

run_test(
    "Normal glucose (105 mg/dL — between 70 and 180)",
    make_payload("dev-thr-n", "p-thr-n", 105.0, 80, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    reject_keys=["alert_glucose"],
)
run_test(
    "High glucose (185 mg/dL → HIGH_GLUCOSE)",
    make_payload("dev-thr-h", "p-thr-h", 185.0, 80, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.HIGH_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "Critical high glucose (260 mg/dL → CRITICAL_HIGH_GLUCOSE)",
    make_payload("dev-thr-ch", "p-thr-ch", 260.0, 80, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.CRITICAL_HIGH_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "Low glucose (65 mg/dL → LOW_GLUCOSE)",
    make_payload("dev-thr-l", "p-thr-l", 65.0, 80, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "Critical low glucose (50 mg/dL → CRITICAL_LOW_GLUCOSE)",
    make_payload("dev-thr-cl", "p-thr-cl", 50.0, 80, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.CRITICAL_LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "Glucose at exact HIGH boundary (180.0 → NORMAL, strict >)",
    make_payload("dev-thr-b", "p-thr-b", 180.0, 80, "good", datetime(2026, 5, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    reject_keys=["alert_glucose"],
)


section("3 · ALERT STATE MACHINE")

run_test(
    "State: NORMAL → LOW fires",
    make_payload("dev-sm-supp", "p-sm-supp", 65.0, 80, "good", datetime(2026, 7, 1, 10, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "State: LOW → LOW suppressed (same state, no re-alert)",
    make_payload("dev-sm-supp", "p-sm-supp", 68.0, 80, "good", datetime(2026, 7, 1, 10, 2, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    reject_keys=["alert_glucose"],
)

run_test(
    "State escalation: NORMAL → LOW fires",
    make_payload("dev-sm-esc", "p-sm-esc", 65.0, 80, "good", datetime(2026, 7, 1, 11, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "State escalation: LOW → CRITICAL_LOW fires (severity increase)",
    make_payload("dev-sm-esc", "p-sm-esc", 50.0, 80, "good", datetime(2026, 7, 1, 11, 2, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.CRITICAL_LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)

run_test(
    "State recovery: NORMAL → LOW fires",
    make_payload("dev-sm-rec", "p-sm-rec", 65.0, 80, "good", datetime(2026, 7, 1, 12, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)
run_test(
    "State recovery: LOW → NORMAL no alert (silent recovery update)",
    make_payload("dev-sm-rec", "p-sm-rec", 105.0, 80, "good", datetime(2026, 7, 1, 13, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    reject_keys=["alert_glucose"],
)
run_test(
    "State recovery: NORMAL → LOW fires again after recovery",
    make_payload("dev-sm-rec", "p-sm-rec", 65.0, 80, "good", datetime(2026, 7, 1, 14, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_keys=["alert_glucose"],
)


section("4 · BATTERY TIERS")

run_test(
    "Battery above low threshold (21% → no battery alert)",
    make_payload("dev-batt-n", "p-batt-n", 105.0, 21, "good", datetime(2026, 5, 1, 13, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    reject_keys=["alert_battery"],
)
run_test(
    "Low battery (15% → LOW_BATTERY)",
    make_payload("dev-batt-l", "p-batt-l", 105.0, 15, "good", datetime(2026, 5, 1, 13, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_keys=["alert_battery"],
)
run_test(
    "Critical battery (8% → CRITICAL_BATTERY)",
    make_payload("dev-batt-c", "p-batt-c", 105.0, 8, "good", datetime(2026, 5, 1, 13, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_keys=["alert_battery"],
)
run_test(
    "Battery escalation step 1: NORMAL → LOW_BATTERY fires",
    make_payload("dev-batt-esc", "p-batt-esc", 105.0, 15, "good", datetime(2026, 5, 1, 14, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_keys=["alert_battery"],
)
run_test(
    "Battery escalation step 2: LOW → CRITICAL fires (severity increase)",
    make_payload("dev-batt-esc", "p-batt-esc", 105.0, 8, "good", datetime(2026, 5, 1, 14, 2, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_keys=["alert_battery"],
)
run_test(
    "Battery escalation step 3: CRITICAL → CRITICAL suppressed (same state)",
    make_payload("dev-batt-esc", "p-batt-esc", 105.0, 8, "good", datetime(2026, 5, 1, 14, 4, 0)),
    expect_status=IngestionStatus.SUCCESS,
    reject_keys=["alert_battery"],
)


section("5 · GLUCOSE TREND ALERTS")

run_test(
    "Rapid drop: >30 mg/dL fall in 15 min (200→160 in 10 min)",
    # Seeded: dev-rdrop/p-rdrop at 08:00 glucose=200; drop to 160 at 08:10 = 40 mg/dL
    make_payload("dev-rdrop", "p-rdrop", 160.0, 80, "good", datetime(2026, 6, 1, 8, 10, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    expect_keys=["alert_trend"],
)
run_test(
    "Rapid rise: >50 mg/dL rise in 30 min (100→160 in 25 min)",
    make_payload("dev-rrise", "p-rrise", 160.0, 80, "good", datetime(2026, 6, 1, 9, 25, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    expect_keys=["alert_trend"],
)
run_test(
    "Statistical spike: >2 stddev above patient historical mean",
    # p004 seeded with tight cluster ~100 mg/dL; 115 is far above mean (~100.4, stdev ~1.1)
    make_payload("dev-d", "p004", 115.0, 80, "good", datetime(2026, 5, 1, 17, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.NORMAL,
    expect_keys=["alert_trend"],
)


section("6 · SUSTAINED CONDITIONS")

run_test(
    "Persistent hypoglycemia: <70 mg/dL sustained for 15+ min (3 readings)",
    # Seeded: p-persis-hypo at 10:00 (65) and 10:05 (67); test at 10:10 (66)
    make_payload("dev-persis-hypo", "p-persis-hypo", 66.0, 80, "good", datetime(2026, 6, 1, 10, 10, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.LOW_GLUCOSE,
    expect_keys=["alert_glucose", "alert_sustained"],
)
run_test(
    "Persistent hyperglycemia: >180 mg/dL for 3+ readings in 30 min (4 readings)",
    # Seeded: p-persis-hyper at 11:00 (200), 11:10 (210), 11:20 (195); test at 11:30 (190)
    make_payload("dev-persis-hyper", "p-persis-hyper", 190.0, 80, "good", datetime(2026, 6, 1, 11, 30, 0)),
    expect_status=IngestionStatus.SUCCESS,
    expect_threshold=AlertType.HIGH_GLUCOSE,
    expect_keys=["alert_glucose", "alert_sustained"],
)


# ─── 7. Device health ─────────────────────────────────────────────────────────
section("7 · DEVICE HEALTH")

run_test(
    "Sensor degraded: 3rd consecutive poor/degraded signal fires alert",
    # Seeded: dev-sensor at 12:00 (poor) and 12:05 (degraded); test at 12:10 (poor) = 3rd
    make_payload("dev-sensor", "p-sensor", 100.0, 80, "poor", datetime(2026, 6, 1, 12, 10, 0)),
    expect_status=IngestionStatus.SUCCESS,
    reject_keys=["alert_glucose"],
    expect_keys=["alert_device"],
)
run_test(
    "Device offline: >15 min gap between readings fires alert (60 min gap)",
    # Seeded: dev-offline last reading at 07:00; test reading at 08:00 = 60 min gap
    make_payload("dev-offline", "p-offline", 100.0, 80, "good", datetime(2026, 6, 1, 8, 0, 0)),
    expect_status=IngestionStatus.SUCCESS,
    reject_keys=["alert_glucose"],
    expect_keys=["alert_device"],
)


print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, ok in results if ok)
for name, ok in results:
    label = PASS if ok else FAIL
    print(f"  [{label}] {name}")
print(f"\n  {passed}/{len(results)} passed")
