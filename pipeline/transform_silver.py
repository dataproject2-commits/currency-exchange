import json
import logging
import psycopg2
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return connection


def validate_rate(rate_value):
    # rate must exist and be greater than 0
    if rate_value is None:
        return False
    if rate_value <= 0:
        return False
    return True


def transform_silver(fetch_date=None):
    if fetch_date is None:
        # use most recent date from Bronze instead of today
        # handles weekends when markets are closed
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(fetch_date) FROM raw_rates")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        fetch_date = result[0] if result[0] else date.today()

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT raw_json FROM raw_rates WHERE fetch_date = %s",
            (fetch_date,)
        )
        row = cursor.fetchone()

        if row is None:
            logger.warning(f"No Bronze data found for {fetch_date}. Skipping Silver transform.")
            return False

        # convert JSON text back to Python list
        raw_json_text = row[0]
        rates_list = json.loads(raw_json_text)

        valid_count = 0
        skipped_count = 0

        for item in rates_list:
            rate_date = item.get("date")
            base_currency = item.get("base")
            target_currency = item.get("quote")
            exchange_rate = item.get("rate")

            if not validate_rate(exchange_rate):
                logger.warning(f"Invalid rate for {target_currency} on {rate_date}. Skipping.")
                skipped_count += 1
                continue

            # skip if this row already exists
            cursor.execute("""
                INSERT INTO cleaned_rates 
                    (date, base_currency, target_currency, exchange_rate)
                VALUES 
                    (%s, %s, %s, %s)
                ON CONFLICT (date, base_currency, target_currency) 
                DO NOTHING
            """, (rate_date, base_currency, target_currency, exchange_rate))

            valid_count += 1

        connection.commit()
        logger.info(f"Silver transform complete for {fetch_date}: "
                   f"{valid_count} rates saved, {skipped_count} skipped")
        cursor.close()
        return True

    except Exception as e:
        connection.rollback()
        logger.error(f"Failed to transform to Silver layer: {e}")
        return False

    finally:
        connection.close()


if __name__ == "__main__":
    print("--- Testing Silver Layer ---")
    success = transform_silver()
    if success:
        print("✓ Silver transform complete!")
    else:
        print("✗ Silver transform failed")