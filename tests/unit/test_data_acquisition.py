"""
Unit tests for the data acquisition module.
"""

import numpy as np
import pandas as pd
import pytest
import yfinance as yf

from src.data_acquisition import (
    download_market_data,
    get_date_range,
    get_exchange_rates,
    validate_market_data,
)


def test_get_date_range():
    """Test date range calculation function."""
    # Test valid inputs
    start, end = get_date_range(2025, 1)
    assert start == "2025-01-01"
    assert end == "2025-01-31"

    # Test February (non-leap year)
    start, end = get_date_range(2025, 2)
    assert start == "2025-02-01"
    assert end == "2025-02-28"

    # Test invalid month
    with pytest.raises(ValueError):
        get_date_range(2025, 13)

    with pytest.raises(ValueError):
        get_date_range(2025, 0)


def fake_yf_download(tickers, start, end, progress, group_by):
    """
    This fake function simulates downloading market data.
    It returns a DataFrame similar to what yfinance.download would return.
    """
    # Generate a business day date range for given period
    dates = pd.date_range(start=start, end=end, freq="B")

    if isinstance(tickers, list) and len(tickers) > 1:
        # Create a MultiIndex DataFrame for multiple tickers with 'Adj Close' information
        data = {}
        for ticker in tickers:
            # Generate synthetic 'Adj Close' prices
            prices = np.random.uniform(100, 200, size=len(dates))
            data[(ticker, "Adj Close")] = pd.Series(prices, index=dates)
        df = pd.DataFrame(data)
        df.columns = pd.MultiIndex.from_tuples(df.columns, names=["Ticker", "Attribute"])
    else:
        # Single ticker returns a DataFrame with a single column
        prices = np.random.uniform(100, 200, size=len(dates))
        df = pd.DataFrame({"Adj Close": prices}, index=dates)

    return df


@pytest.fixture(autouse=True)
def patch_yfinance_download(monkeypatch):
    """
    Automatically patch yf.download with fake_yf_download for these tests.
    """
    monkeypatch.setattr(yf, "download", fake_yf_download)


def test_download_market_data():
    """Test market data download function using a fake data source."""
    start_date = "2024-01-01"
    end_date = "2024-01-05"
    tickers = ["AAPL"]

    # Call the function under test
    prices = download_market_data(tickers, start_date, end_date)

    # Check that the returned DataFrame is not empty and has the correct type
    assert isinstance(prices, pd.DataFrame) or isinstance(prices, pd.Series)
    assert not prices.empty

    # Ensure that the index of the prices is a DatetimeIndex for further processing
    assert isinstance(prices.index, pd.DatetimeIndex)


def test_get_exchange_rates():
    """Test exchange rate retrieval function."""
    start_date = "2025-01-01"
    end_date = "2025-01-31"

    # Test simulated rates
    rates = get_exchange_rates(start_date, end_date, simulation=True)

    assert isinstance(rates, pd.Series)
    assert not rates.empty
    assert rates.index.is_monotonic_increasing
    assert rates.index.dtype == "datetime64[ns]"
    assert rates.name == "USD/CAD"
    assert all(rate > 0 for rate in rates)

    # Test that non-simulation mode raises NotImplementedError
    with pytest.raises(NotImplementedError):
        get_exchange_rates(start_date, end_date, simulation=False)


def test_validate_market_data():
    """Test market data validation function."""
    # Test case 1: Valid data
    dates = pd.date_range(start="2025-01-01", end="2025-01-31", freq="B")
    valid_data = pd.DataFrame({
        'AAPL': np.random.uniform(100, 110, len(dates)),
        'GOOGL': np.random.uniform(2500, 2600, len(dates)),
        'SPY': np.random.uniform(400, 410, len(dates))
    }, index=dates)
    assert validate_market_data(valid_data) is True

    # Test case 2: Missing values
    data_with_missing = valid_data.copy()
    data_with_missing.iloc[0, 0] = None
    assert not validate_market_data(data_with_missing)

    # Test case 3: Zero values
    data_with_zeros = valid_data.copy()
    data_with_zeros.iloc[0, 0] = 0
    assert not validate_market_data(data_with_zeros)

    # Test case 4: Negative values
    data_with_negative = valid_data.copy()
    data_with_negative.iloc[0, 0] = -1
    assert not validate_market_data(data_with_negative)

    # Test case 5: Empty DataFrame
    empty_data = pd.DataFrame()
    assert not validate_market_data(empty_data)
