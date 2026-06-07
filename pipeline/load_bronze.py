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
    # reads credentials from .env file
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return connection


def already_fetched_today(connection, fetch_date):
    # check if data already exists for this date and avoid duplicates
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM raw_rates WHERE fetch_date = %s",
        (fetch_date,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    return count > 0


def load_bronze(raw_data, fetch_date=None):
    if fetch_date is None:
        fetch_date = date.today()

    connection = get_db_connection()

    try:
        if already_fetched_today(connection, fetch_date):
            logger.info(f"Data for {fetch_date} already exists in Bronze. Skipping.")
            return False

        cursor = connection.cursor()

        # saves raw JSON exactly as it came from the API
        raw_json_text = json.dumps(raw_data)

        cursor.execute("""
            INSERT INTO raw_rates (fetch_date, base_currency, raw_json)
            VALUES (%s, %s, %s)
        """, (fetch_date, "USD", raw_json_text))

        connection.commit()
        logger.info(f"Successfully saved raw data for {fetch_date} to Bronze layer")
        cursor.close()
        return True

    except Exception as e:
        connection.rollback()
        logger.error(f"Failed to save to Bronze layer: {e}")
        return False

    finally:
        connection.close()


if __name__ == "__main__":
    from extract import fetch_rates

    print("--- Testing Bronze Layer ---")
    raw_data = fetch_rates()

    if raw_data:
        success = load_bronze(raw_data)
        if success:
            print("✓ Data successfully saved to Bronze layer!")
        else:
            print("✗ Data was not saved - it may already exist for today")
    else:
        print("✗ Could not fetch data from API")