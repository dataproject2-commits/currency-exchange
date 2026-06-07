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


def ensure_date_dimension(cursor, rate_date):
    # 1=Monday, 7=Sunday so less than 6 means weekday
    is_weekday = rate_date.isoweekday() < 6

    cursor.execute("""
        INSERT INTO dim_dates (date, year, month, day, is_weekday)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (date) DO NOTHING
    """, (
        rate_date,
        rate_date.year,
        rate_date.month,
        rate_date.day,
        is_weekday
    ))


def transform_gold(fetch_date=None):
    if fetch_date is None:
        # use most recent date from Silver instead of today
        # handles weekends when markets are closed
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(date) FROM cleaned_rates")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        fetch_date = result[0] if result[0] else date.today()

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT date, base_currency, target_currency, exchange_rate
            FROM cleaned_rates
            WHERE date = %s
        """, (fetch_date,))

        rows = cursor.fetchall()

        if not rows:
            logger.warning(f"No Silver data found for {fetch_date}. Skipping Gold transform.")
            return False

        saved_count = 0

        for row in rows:
            rate_date, base_currency, target_currency, exchange_rate = row

            ensure_date_dimension(cursor, rate_date)

            # get previous day's rate to calculate change
            cursor.execute("""
                SELECT exchange_rate 
                FROM cleaned_rates
                WHERE target_currency = %s
                AND base_currency = %s
                AND date < %s
                ORDER BY date DESC
                LIMIT 1
            """, (target_currency, base_currency, rate_date))

            prev_row = cursor.fetchone()

            if prev_row:
                prev_rate = prev_row[0]
                # formula: ((today - yesterday) / yesterday) * 100
                rate_change_pct = ((exchange_rate - prev_rate) / prev_rate) * 100
            else:
                rate_change_pct = None

            # average of last 7 days for this currency
            cursor.execute("""
                SELECT AVG(exchange_rate)
                FROM (
                    SELECT exchange_rate
                    FROM cleaned_rates
                    WHERE target_currency = %s
                    AND base_currency = %s
                    AND date <= %s
                    ORDER BY date DESC
                    LIMIT 7
                ) AS last_7_days
            """, (target_currency, base_currency, rate_date))

            avg_row = cursor.fetchone()
            seven_day_avg = avg_row[0] if avg_row else None

            cursor.execute("""
                INSERT INTO aggregated_rates
                    (date, base_currency, target_currency, 
                     exchange_rate, rate_change_pct, seven_day_avg)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (date, base_currency, target_currency)
                DO NOTHING
            """, (
                rate_date,
                base_currency,
                target_currency,
                exchange_rate,
                rate_change_pct,
                seven_day_avg
            ))

            saved_count += 1

        connection.commit()
        logger.info(f"Gold transform complete for {fetch_date}: {saved_count} rates saved")
        cursor.close()
        return True

    except Exception as e:
        connection.rollback()
        logger.error(f"Failed to transform to Gold layer: {e}")
        return False

    finally:
        connection.close()


if __name__ == "__main__":
    print("--- Testing Gold Layer ---")
    success = transform_gold()
    if success:
        print("✓ Gold transform complete!")
    else:
        print("✗ Gold transform failed")