# Currency Exchange Data Pipeline

This is automated data pipeline project that fetches currency 
exchange rates every day and stores them in a PostgreSQL database using Medallion 
Architecture (Bronze → Silver → Gold).

## What This Project Does

Every day at 08:00 AM Tashkent time (03:00 UTC), the pipeline 
automatically fetches exchange rates from the Frankfurter API and 
transforms them through three layers:

- Bronze: saves raw data exactly as it came from the API
- Silver: cleans and validates the data
- Gold: calculates metrics like day-over-day change and 7-day averages

The following currencies are tracked against USD:

| Currency | Name |
|----------|------|
| EUR | Euro |
| GBP | British Pound |
| RUB | Russian Ruble |
| UZS | Uzbek Som |

## Project Structure
currency-exchange/
├── pipeline/
│   ├── extract.py
│   ├── load_bronze.py
│   ├── transform_silver.py
│   ├── transform_gold.py
│   ├── backfill.py
│   └── scheduler.py
├── sql/
│   └── schema.sql
├── tests/
│   └── test_transformations.py
├── .env.example
├── requirements.txt
└── README.md

## Setup Instructions

### 1. Requirements
- Python 3.10+
- PostgreSQL 18
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/dataproject2-commits/currency-exchange.git
cd currency-exchange
```

### 3. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
```bash
copy .env.example .env
```

Edit `.env` with your real database credentials:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=currency_db
DB_USER=postgres
DB_PASSWORD=your_password_here
BASE_CURRENCY=USD
TARGET_CURRENCIES=UZS,RUB,EUR,GBP
```

### 6. Set Up the Database
```bash
psql -U postgres
```
```sql
CREATE DATABASE currency_db;
\c currency_db
```
Then run everything inside `sql/schema.sql`.

## How to Run

### Load Historical Data (run once)
```bash
python pipeline/backfill.py
```

### Run the Scheduler
```bash
python pipeline/scheduler.py
```

The scheduler runs the pipeline immediately on startup, then every day 
at 03:00 UTC automatically. Press Ctrl+C to stop.

## Running Tests
```bash
python -m pytest tests/ -v
```
11 tests should pass.

## Architecture Decisions

- Used Python's `schedule` library for scheduling (not APScheduler) because 
  it is lightweight and sufficient for a single daily job
- Used Frankfurter v2 API instead of v1 because v1 does not support 
  UZS and RUB
- Bronze layer is never modified once written, it works as an audit log
- All transformations are written in Python instead of SQL views because 
  Python is easier to test and debug
- USD is used as base currency because it is the world reserve currency
- Pipeline checks for existing data before inserting to avoid duplicates

## Assumptions

- Rates are fetched once per day
- Non-trading days like weekends are skipped gracefully
- Bronze data is never deleted or modified
- Historical data loaded from January 1, 2025