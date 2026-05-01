# Medivue — Design Document
Author: Quan (Tony) Pham

The repository is segregated into four layers: api, service, storage, and models, all these are in src folder. script folder represents the scripts to initialize/seed the database, and contains a light-weight makeshift testing framework for I/O validations. data folder contains .db files the SQLite.

```
src/
├── api/          # HTTP controllers - request parsing, response export
├── service/      # Business logic - ingestion pipeline, validation, alerting, export message construction
├── storage/      # State management - SQLite schema, in-memory session store
├── models/       # Data contracts - Pydantic payloads, enums, device abstractions
├── config.py     # Single source of truth for all constants and thresholds
scripts/
├── seed.py       # Populates test data for development
└── test.py       # Integration test suite
```

Controllers know nothing about alert logic. Services know nothing about HTTP. Storage knows nothing about business rules. This strict layering means any layer can be replaced without touching the others, where swapping SQLite for Postgres only requires changes in `storage/`, adding a real SMS transport only requires implementing `send_alert()` in `models/devices.py`.

`config.py` centralises every threshold and constant.

The alert class hierarchy (`Alert` -> `GlucoseAlert`, `BatteryAlert`, `DeviceHealthAlert`, `LateReadingAlert`) and the device abstraction (`CommunicationDevice` -> `Mobile` / `Computer`) are both designed as extension points. New alert types and new transport channels can be added without modifying the ingestion pipeline or the state machine.



## Assumptions

- The GMS is designed to manage "low patient counts", where overheads that can be traced back to high patient counts (such as high readings in short periods of time) will be armotised, as it is assuming a low patient count would not meaningfully affect the system's performance. 

- The system is designed as a proof-of-concept / prototype rather than production-ready software repository. Many decisions are made to support development and testing quality-of-life, rather than to optimise for production performance

- The system is assumed to be a monolithic program, and that it would not need to interact with external servers such as load balancers, peer systems, etc...

- Readings are NOT concurrent. Each reading triggers its own validation, storage, and alert evaluation synchronously. This keeps the response payload informative per-reading, which is useful during development and testing. There is no explicit handlers for concurrent reads as of yet.

- The timestamp on the reading reflects when the device actually recorded the glucose value. 

- Alert dispatch is fire-and-forget. For simplicity sake for this prototype, there is no acknowledgment, retry, or delivery confirmation. Devices are stubs that print to terminal as a place holder for future extensions. The interface is defined so real transports slot in without touching alert logic.

- Critical threshold assumes a magic ratio of 20% past initial threshold, can be configured in config.py

- Glucose bounds are to be adjusted manually by clinicians, and are rarely changed.

- Device clocks may drift. The system trusts `recorded_at` as the authoritative event time for all clinical analysis, and uses `arrival_time` (captured at the server on receipt) only to detect transmission latency. This means a reading with a drifted clock is still placed correctly in historical time-windows — the analysis is never corrupted by when the reading arrived.

- Duplicate readings are identified by `(device_id, recorded_at)`, and by no other identification methods within the payload. 


---

## Data Model

 `readings` is the core fact table: device, patient, glucose, battery, signal quality, and `recorded_at`. All time-series queries query this table filtered and ordered by `recorded_at`. Two indexes cover the common access patterns: `(device_id, recorded_at)` for device-scoped queries, and `(patient_id)` for patient-scoped aggregations.
  
  Indexing is introduced to prevent full-table scan for every trend-detection or time-series queries made, improving latency.

  Composite index `(device_id, recorded_at)` covers 3 queries that filter by device and time together:
    * has_duplicate
    * get_last_reading_time
    * get_recent_signal_qualities
  All 3 queries can be satisfied with one B-tree lookup in the DB, reducing latency and improving query overhead. 
  Trade off to using index is every INSERT into readings must update both indexes in addition to the table itself. This system assumes that it will be managing "low patient count", hence, the trade-off for higher INSERT overhead for better look-up performance is chosen. The system also chooses not to implement bulk ingestion, so persistent indexing is supported. Should bulk ingestion be implemented and without modification, the system would pay index update cost for every row in the batch (High latency for every bulk ingested). To resolve this, indexes would be dropped, ingest bulk, then rebuild indexes.

`patient_glucose` stores configurable glucose bounds per patient. It is queried on every reading to resolve the normal range for that patient, with a fallback to global config constants when no row exists.`patient_id` is UNIQUE, so the implicit B-tree index makes lookups O(log n) without a separate index declaration. The trade-off is a DB round-trip on every ingested reading. Since bounds are set by a clinician and changes rarely, a lazy in-memory dict (populated on first lookup per patient, keyed by `patient_id`) would reduce this to O(1) with no further DB cost. The trade-off is staleness, as in a bounds update would not take effect until the cache is invalidated or the server restarts. For this prototype, always-fresh DB reads were chosen for correctness simplicity; the cache is the natural next step. A further extension would be versioned bounds with an effective-date column, so the system could apply the bounds that were active at the time a reading was recorded rather than the current bounds.

SQLite was chosen because it requires zero operational overhead, ships with Python, and supports the indexed queries this system needs. The prototype runs on a single server with low patient count where there is no concurrent write pressure that would expose SQLite's single-writer limitation. Any production deployment would replace it with Postgres and a connection pool to gain concurrent writes, connection pooling, and horizontal scaling.

`alert_states` persists the state machine. Each row is keyed on `(patient_id, device_id, category)` and stores the current alert type and when it last fired. Persisting this to SQLite means the suppression and cooldown logic survives server restarts, so that a repeated alert doesn't re-fire just because the process restarted. The trade-off is a write on every state transition, adding write pressure to SQLite under high reading volume. This trade-off is preferred as it is assumed that the system will handle low-patient/low read counts. `INSERT` or `REPLACE` overwrites the existing row rather than appending, so the table stays bounded at one row per alert channel per device per patient rather than growing unboundedly. The current design stores only the latest state, which means alert history is NOT persistent. This design was chosen for simplicity-sake for this prototype, bounded table size and O(1) state lookup. The extension to this is an append-only "alert_events" table that records every transition with a timestamp, keeping `alert_states` as a fast current-state cache and `alert_events` as the durable audit trail. At higher scale, this table is where SQLite would probably bottleneck first, as it is written on every reading regardless of whether an alert fires. Future extension to resolve this could be Redis where atomic SETNX for cooldown enforcement and a TTL on the cooldown key eliminates the need to store and compare `fired_at` timestamps manually.


---

## Alerting Strategy

Each reading runs through six independent detection channels: 
glucose threshold --> glucose trend --> sustained glucose condition --> battery level --> device health -- > late arrival.

Each channel produces an `AlertType` which is fed into a shared state machine before anything is dispatched.

An alert is opened when `should_fire()` determines the new state differs meaningfully from the current state and the cooldown window has elapsed. The state and timestamp are written to `alert_states`, and the alert is dispatched to the patient's doctor/nurses/admin registered devices. An alert is "supressed" when the same state repeats within the 15-minute cooldown — the state is silently updated but nothing is dispatched, preventing alert fatigue. An alert is "escalated"when severity increases (`LOW_GLUCOSE` to `CRITICAL_LOW_GLUCOSE`) and bypasses all cooldown timer. An alert is "resolved "silently such as when the channel returns `NORMAL`, the state is updated without dispatching a recovery notification. 

This means clinicians are only paged when something changes meaningfully. A patient holding steady at a high-but-not-critical glucose does not generate repeated alerts every five minutes. This design is chosen so that the system does not flood personnel with unimportant alerts that would cause constant disruption for the hospital in a practical setting. It aims to only alert when anything meaningful occurs.

At a higher scale, the current design evaluates all six channels synchronously per request and writes alert state to SQLite on every reading. This becomes a bottleneck under concurrent load. The natural decomposition is to publish readings to a queue such as Kafka and run alert evaluation as a separate consumer, with alert state held in Redis rather than SQLite. Redis atomic operations (SETNX, GETSET) map onto the check-and-fire pattern without locks.


## Out-of-Order Ingestion

The spec states devices may send readings up to 15 minutes late or out of sequence. This system handles it by anchoring all time-window analysis to `recorded_at` (event time) rather than arrival order. Every query that detects trends, sustained conditions, or device gaps filters and orders by `recorded_at`:

```
WHERE patient_id = ? AND recorded_at >= ?   -- trend/sustained windows
WHERE device_id  = ? AND recorded_at < ?    -- device gap detection
```

A reading that arrives 40 minutes after it was recorded is stored with its original `recorded_at`. When the next reading arrives, all historical queries correctly include the late reading in its proper position in the time series. The clinical analysis is never corrupted by arrival order.

An append-only model stores readings in insertion order and queries by row sequence or insertion timestamp. This is simpler because there is no need to distinguish two timestamps, but gives wrong answers when readings arrive out of order. A trend window that queries "the last 15 minutes by insertion order" would exclude a delayed reading that physiologically belongs in that window. For a CGM system where trend detection (rapid drop, rapid rise) is a safety feature, hence, the trade-off for append-only model is NOT recommended.

If two readings arrive within the same processing window (milliseconds) and the older one arrives second, the first reading's trend check will not have seen the second reading yet — it is not in the database at that moment. In practice, CGM devices transmit every 5 minutes, so simultaneous out-of-order arrivals are unlikely. A full solution would buffer readings for a short grace period before evaluating them, at the cost of alert latency. This was not implemented.

---

## additional trade-offs

`session_memory` holds the per-patient alert queue in a bounded deque. For this prototype, in-memory storage is preferred for development speed, lower complexity, and fast, but it is lost on server restart and is NOT persistent. For the export endpoint, this means a server restart clears recent alert context. In production this queue would be backed by Redis or written to the database so the summary endpoint always reflects true history.

Every reading queries `patient_glucose` to resolve glucose bounds. Since patient bounds are set by a clinician and rarely change, a lazy in-memory map (populated on first read from a persistent JSON file, keyed by `patient_id`) would reduce this to O(1) with no DB round-trip after the first lookup. The trade-off is that a bounds update would not take effect until the cache is invalidated or the server restarts, and that the JSON file is manually updated.

---

## What I'd Change With More Time / Changes for a production environment

- Structured logging. Every alert dispatch currently calls `print()`. Production would require structured logs (JSON, with patient ID, device ID, alert type, timestamp) for auditing and query management purposes.

- Real transport layer The `CommunicationDevice` interface is defined to represent a communication endpoint for alerts to be sent to. Adding an SMS or push provider is a matter of implementing `send_alert()`. In a real production, wiring to real transport and adding retry logic with exponential backoff would be required.

-The API has no auth. In a clinical context authorisation is required for safe practices and to prevent cybersecurity attacks. The ingestion endpoint should require device credentials and the summary endpoint should be scoped to authorized staff.

- `query_readings` currently returns the last 24 hours of readings with no limit beyond what the caller slices. Under a high-frequency device this could return thousands of rows. In production, a cursor-based pagination would be implemented at endpoint.

- Schema is initialized with `CREATE TABLE IF NOT EXISTS`. Any schema change requires manual intervention. A migration tool (Alembic) would make schema evolution safe and auditable.


- The patient model is intentionally minimal. The spec suggests a `diagnosis` field as one example of a per-patient instance. I implemented the underlying intent where per-patient glucose bounds (`lower_bound`, `upper_bound`) are stored in `patient_glucose` without adding a diagnosis enum or demographic fields, which are out of scope for this prototype. What a production patient record would additionally need:
   demographics (name, DOB, MRN), assigned clinical staff, device registration, and an audit log of bound changes. None of these were modelled.