import requests
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Frankfurter v2 API, supports UZS and RUB 
API_BASE_URL = "https://api.frankfurter.dev/v2/rates"
BASE_CURRENCY = "USD"
TARGET_CURRENCIES = "EUR,GBP,RUB,UZS"


# retries up to 3 times if API call fails
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def fetch_rates(date=None):
    params = {
        "base": BASE_CURRENCY,
        "quotes": TARGET_CURRENCIES
    }

    # add date only if provided, otherwise API returns latest
    if date:
        params["date"] = date

    logger.info(f"Fetching rates for date: {date if date else 'latest'}")

    response = requests.get(API_BASE_URL, params=params, timeout=10)

    # 200 means success
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Successfully fetched {len(data)} rates")
        return data
    else:
        logger.error(f"API request failed with status code: {response.status_code}")
        return None


if __name__ == "__main__":
    print("\n--- Testing latest rates ---")
    latest = fetch_rates()
    if latest:
        for item in latest:
            print(f"1 {item['base']} = {item['rate']} {item['quote']}")

    print("\n--- Testing historical rates ---")
    historical = fetch_rates(date="2025-01-15")
    if historical:
        for item in historical:
            print(f"1 {item['base']} = {item['rate']} {item['quote']}")