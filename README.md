# Medivue — CGM Ingestion & Alerting System

## Setup

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


## Run


uvicorn src.main:app --reload


Interactive docs at `http://localhost:8000/docs`.

## Seed & Test

python scripts/seed.py   # populate test data
python scripts/test.py   # run integration tests
