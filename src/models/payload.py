from pydantic import BaseModel
from datetime import datetime


class READING_PAYLOAD(BaseModel):
    glucose_mgdl: float
    battery_pct: int
    signal_quality: str  # "good" | "poor" | "degraded"
    recorded_at: datetime


class READING_WRAPPER(BaseModel):
    device_id: str
    patient_id: str
    reading: READING_PAYLOAD