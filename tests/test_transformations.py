import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pipeline'))

from transform_silver import validate_rate
from extract import fetch_rates


def test_valid_rate():
    assert validate_rate(11962.0) == True

def test_zero_rate_is_invalid():
    assert validate_rate(0) == False

def test_negative_rate_is_invalid():
    assert validate_rate(-5.0) == False

def test_none_rate_is_invalid():
    assert validate_rate(None) == False

def test_small_valid_rate():
    assert validate_rate(0.0001) == True


def test_fetch_rates_returns_list():
    result = fetch_rates()
    assert isinstance(result, list)

def test_fetch_rates_returns_four_currencies():
    result = fetch_rates()
    assert len(result) == 4

def test_fetch_rates_has_correct_keys():
    result = fetch_rates()
    for item in result:
        assert "date" in item
        assert "base" in item
        assert "quote" in item
        assert "rate" in item

def test_fetch_rates_base_is_usd():
    result = fetch_rates()
    for item in result:
        assert item["base"] == "USD"

def test_fetch_rates_all_rates_positive():
    result = fetch_rates()
    for item in result:
        assert item["rate"] > 0

def test_fetch_historical_rate():
    result = fetch_rates(date="2025-01-15")
    assert result is not None
    assert len(result) == 4