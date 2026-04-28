import sqlite3

DB_PATH = "data/cgm.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            patient_id TEXT,
            glucose REAL,
            battery_pct INTEGER,
            signal_quality TEXT,
            recorded_at TEXT
        )
    """)

    conn.commit()
    conn.close()