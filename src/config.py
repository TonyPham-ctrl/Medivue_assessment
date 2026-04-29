
# Database
DB_READING_PATH = "data/cgm.db"
DB_PATIENT_GLUCOSE_PATH = "data/patient_glucose.db"
DB_READING_TABLE = "readings"
DB_PATIENT_GLUCOSE_TABLE = "patient_glucose"

# Validation
VALID_SIGNAL_QUALITIES = ["good", "poor", "degraded"]
BATTERY_PCT_MIN = 0
BATTERY_PCT_MAX = 20
GLUCOSE_MGDL_MIN = 0

# Statistical anomaly detection
STAT_MIN_SAMPLES = 3
STAT_ANOMALY_STDDEV_MULTIPLIER = 2

# Session memory
MAX_SESSION_SIZE = 100

# App
APP_TITLE = "CGM Monitoring System"
APP_DESCRIPTION = "Hello Medivue"
APP_VERSION = "1.0.0"
