
from src.models.enums import IngestionStatus
# Database
DB_PATH = "data/medivue.db"
DB_READING_TABLE = "readings"
DB_PATIENT_GLUCOSE_TABLE = "patient_glucose"

# Validation
VALID_SIGNAL_QUALITIES = ["good", "poor", "degraded"]
GLUCOSE_MGDL_MIN = 0

# Glucose safety thresholds (mg/dL)
GLUCOSE_CRITICAL_LOW = 54
GLUCOSE_LOW = 70
GLUCOSE_HIGH = 180
GLUCOSE_CRITICAL_HIGH = 250

# Battery
BATTERY_PCT_LOW_THRESHOLD = 20
BATTERY_PCT_CRITICAL_THRESHOLD = 10

# Statistical anomaly detection
STAT_MIN_SAMPLES = 3
STAT_ANOMALY_STDDEV_MULTIPLIER = 2

# Sustained glucose conditions
SUSTAINED_HYPO_MINUTES = 15
SUSTAINED_HYPER_MINUTES = 30
SUSTAINED_HYPER_MIN_READINGS = 3

# Rapid change detection
RAPID_DROP_MGDL = 30
RAPID_DROP_MINUTES = 15
RAPID_RISE_MGDL = 50
RAPID_RISE_MINUTES = 30

# Device health
SIGNAL_POOR_STREAK_COUNT = 3
DEVICE_OFFLINE_MINUTES = 15

# Alert state machine
ALERT_COOLDOWN_MINUTES = 15
LATE_READING_THRESHOLD_MINUTES = 15

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

# Alert queue size limit
MAX_QUEUE_SIZE = 100