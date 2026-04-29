
from src.models.enums import IngestionStatus
# Database
DB_PATH = "data/medivue.db"
DB_READING_TABLE = "readings"
DB_PATIENT_GLUCOSE_TABLE = "patient_glucose"

# Validation
VALID_SIGNAL_QUALITIES = ["good", "poor", "degraded"]
GLUCOSE_MGDL_MIN = 0

# Battery
BATTERY_PCT_LOW_THRESHOLD = 20

# Statistical anomaly detection
STAT_MIN_SAMPLES = 3
STAT_ANOMALY_STDDEV_MULTIPLIER = 2

# App
APP_TITLE = "CGM Monitoring System"
APP_DESCRIPTION = "Hello Medivue"
APP_VERSION = "1.0.0"

_STATUS_MAP = {
    IngestionStatus.SUCCESS: 200,
    IngestionStatus.INVALID: 400,
    IngestionStatus.DUPLICATE: 409,
    IngestionStatus.ERROR: 500,
}