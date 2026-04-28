
import sqlite3
from src.storage.sqlite_db import DB_PATH


def is_duplicate(device_id, recorded_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM readings
        WHERE device_id = ? AND recorded_at = ?
    """, (device_id, str(recorded_at)))

    count = cursor.fetchone()[0]
    conn.close()

    return count > 0

def validate_post_payload(payload):
    response_message = ""
    response_status = 200
    if not payload.device_id or not isinstance(payload.device_id, str):
        response_message += "device_id must be a non-empty string \n"
        response_status = 400

    if not payload.patient_id or not isinstance(payload.patient_id, str):
        response_message += "patient_id must be a non-empty string \n"
        response_status = 400

    if payload.reading.glucose_mgdl <= 0:
        response_message += "glucose_mgdl must be a positive number \n"
        response_status = 400

    if not (0 <= payload.reading.battery_pct <= 100):
        response_message += "battery_pct must be between 0 and 100 \n"
        response_status = 400

    if payload.reading.signal_quality not in ["good", "poor", "degraded"]:
        response_message += "signal_quality must be 'good', 'poor', or 'degraded' \n"
        response_status = 400

    if is_duplicate(payload.device_id, payload.reading.recorded_at):
        response_message += "Duplicate reading detected \n"
        response_status = 409

    return response_status, response_message