import logging
from datetime import date, timedelta
from dotenv import load_dotenv

from extract import fetch_rates
from load_bronze import load_bronze
from transform_silver import transform_silver
from transform_gold import transform_gold

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_backfill(start_date, end_date):
    total_days = (end_date - start_date).days + 1
    logger.info(f"Starting backfill from {start_date} to {end_date} ({total_days} days)")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    current_date = start_date

    while current_date <= end_date:
        logger.info(f"Processing {current_date}...")

        raw_data = fetch_rates(date=str(current_date))

        # no data means weekend or holiday, skip it
        if raw_data is None:
            logger.warning(f"No data for {current_date} - likely a non-trading day. Skipping.")
            skipped_count += 1
            current_date += timedelta(days=1)
            continue

        bronze_success = load_bronze(raw_data, fetch_date=current_date)

        if not bronze_success:
            # data already exists for this date
            logger.info(f"Data for {current_date} already exists. Skipping.")
            skipped_count += 1
            current_date += timedelta(days=1)
            continue

        silver_success = transform_silver(fetch_date=current_date)

        if not silver_success:
            logger.error(f"Silver transform failed for {current_date}")
            failed_count += 1
            current_date += timedelta(days=1)
            continue

        gold_success = transform_gold(fetch_date=current_date)

        if not gold_success:
            logger.error(f"Gold transform failed for {current_date}")
            failed_count += 1
            current_date += timedelta(days=1)
            continue

        success_count += 1
        current_date += timedelta(days=1)

    logger.info(f"Backfill complete!")
    logger.info(f"  Successful: {success_count} days")
    logger.info(f"  Skipped:    {skipped_count} days (already existed or non-trading)")
    logger.info(f"  Failed:     {failed_count} days")


if __name__ == "__main__":
    end = date.today()
    start = date(2025, 1, 1)

    print(f"--- Starting Historical Backfill ---")
    print(f"From: {start}")
    print(f"To:   {end}")
    print(f"This may take a few minutes...")
    print()

    run_backfill(start, end)