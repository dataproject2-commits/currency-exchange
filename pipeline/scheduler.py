import logging
import schedule
import time
from datetime import date
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


def run_pipeline():
    today = date.today()
    logger.info(f"=== Pipeline started for {today} ===")

    logger.info("Step 1: Fetching data from API...")
    raw_data = fetch_rates()

    if raw_data is None:
        logger.error("Failed to fetch data from API. Pipeline stopped.")
        return

    logger.info("Step 2: Saving to Bronze layer...")
    bronze_success = load_bronze(raw_data)

    if not bronze_success:
        # data may already exist for today, continue anyway
        logger.warning("Bronze layer skipped - data may already exist for today.")

    logger.info("Step 3: Transforming to Silver layer...")
    silver_success = transform_silver()

    if not silver_success:
        logger.error("Silver transform failed. Pipeline stopped.")
        return

    logger.info("Step 4: Transforming to Gold layer...")
    gold_success = transform_gold()

    if not gold_success:
        logger.error("Gold transform failed. Pipeline stopped.")
        return

    logger.info(f"=== Pipeline completed successfully for {today} ===")


# runs every day at 03:00 UTC that is 08:00 Tashkent time
schedule.every().day.at("03:00").do(run_pipeline)

logger.info("Scheduler started!")
logger.info("Pipeline will run every day at 03:00 UTC (08:00 Tashkent time)")
logger.info("Press Ctrl+C to stop the scheduler")


if __name__ == "__main__":
    # run immediately on startup, then wait for scheduled time
    logger.info("Running pipeline immediately on startup...")
    run_pipeline()

    while True:
        schedule.run_pending()
        time.sleep(60)