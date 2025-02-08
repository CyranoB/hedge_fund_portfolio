"""
Integration tests for the data acquisition module.
These tests make actual API calls and should be run separately from unit tests.
"""

from datetime import datetime

import pandas as pd
import pytest

from src.config import LONG_TICKERS, MARKET_INDEX, SHORT_TICKERS
from src.data_acquisition import download_market_data, validate_market_data

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def test_download_market_data_real():
    """Test market data download with real API calls."""
    # Use a small set of tickers and a short date range to minimize API usage
    tickers = LONG_TICKERS[:2] + SHORT_TICKERS[:2] + [MARKET_INDEX]
    start_date = "2024-01-01"
    end_date = "2024-01-31"  # Extended to full month to ensure enough trading days

    # Download data
    prices = download_market_data(tickers, start_date, end_date)

    # Verify the result
    assert isinstance(prices, pd.DataFrame)
    assert not prices.empty
    assert isinstance(prices.index, pd.DatetimeIndex)
    assert all(ticker in prices.columns for ticker in tickers)

    # Verify data quality
    assert validate_market_data(prices)

    # Verify date range
    assert prices.index[0].strftime("%Y-%m-%d") >= start_date
    assert prices.index[-1].strftime("%Y-%m-%d") <= end_date


def test_download_market_data_error_handling():
    """Test error handling with invalid tickers."""
    invalid_tickers = ["INVALID1", "INVALID2"]
    start_date = "2024-01-01"
    end_date = "2024-01-05"

    with pytest.raises(ValueError):
        download_market_data(invalid_tickers, start_date, end_date)
