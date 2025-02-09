"""Integration tests for data acquisition functionality."""

import pytest
from datetime import datetime
from src.data_acquisition import download_market_data
from src.config import LONG_TICKERS, SHORT_TICKERS, MARKET_INDEX

def test_download_market_data_integration():
    """Test downloading market data from the API."""
    tickers = LONG_TICKERS + SHORT_TICKERS + [MARKET_INDEX]
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    market_data = download_market_data(tickers, start_date, end_date)
    
    assert not market_data.empty
    assert all(ticker in market_data.columns for ticker in tickers)
    assert len(market_data) > 0
    assert market_data.index.is_monotonic_increasing
    assert not market_data.isnull().any().any()

def test_download_market_data_error_handling():
    """Test error handling when downloading market data."""
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    with pytest.raises(ValueError):
        download_market_data(["INVALID_TICKER"], start_date, end_date)

    with pytest.raises(ValueError):
        download_market_data([], start_date, end_date)

    with pytest.raises(TypeError):
        download_market_data(None, start_date, end_date)

def test_download_market_data_date_range():
    """Test downloading market data for specific date range."""
    tickers = LONG_TICKERS + SHORT_TICKERS + [MARKET_INDEX]
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    market_data = download_market_data(tickers, start_date, end_date)
    
    assert market_data.index.dtype == 'datetime64[ns]'
    assert len(market_data) >= 15  # At least 15 trading days
    assert (market_data > 0).all().all()  # All prices should be positive 