"""
Unit tests for the data acquisition module.
"""

import pytest
import pandas as pd
from datetime import datetime
from src.data_acquisition import get_date_range, download_market_data, get_exchange_rates, validate_market_data

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

def test_download_market_data():
    """Test market data download function."""
    # Test with a single ticker for a short period
    start_date = "2024-01-01"
    end_date = "2024-01-05"
    tickers = ["AAPL"]
    
    df = download_market_data(tickers, start_date, end_date)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.index.is_monotonic_increasing
    assert df.index.dtype == 'datetime64[ns]'
    assert all(ticker in df.columns for ticker in tickers)

def test_get_exchange_rates():
    """Test exchange rate retrieval function."""
    start_date = "2025-01-01"
    end_date = "2025-01-31"
    
    # Test simulated rates
    rates = get_exchange_rates(start_date, end_date, simulation=True)
    
    assert isinstance(rates, pd.Series)
    assert not rates.empty
    assert rates.index.is_monotonic_increasing
    assert rates.index.dtype == 'datetime64[ns]'
    assert rates.name == 'USD/CAD'
    assert all(rate > 0 for rate in rates)
    
    # Test that non-simulation mode raises NotImplementedError
    with pytest.raises(NotImplementedError):
        get_exchange_rates(start_date, end_date, simulation=False)

def test_validate_market_data():
    """Test market data validation function."""
    # Create a valid DataFrame
    dates = pd.date_range(start="2025-01-01", end="2025-01-31", freq='B')
    valid_data = pd.DataFrame({
        'AAPL': range(1, len(dates) + 1),
        'MSFT': range(2, len(dates) + 2)
    }, index=dates)
    
    assert validate_market_data(valid_data) == True
    
    # Test with missing values
    invalid_data = valid_data.copy()
    invalid_data.iloc[0, 0] = None
    assert validate_market_data(invalid_data) == False
    
    # Test with insufficient trading days
    short_data = valid_data.iloc[:5]
    assert validate_market_data(short_data) == False
    
    # Test with zero prices
    zero_data = valid_data.copy()
    zero_data.iloc[0, 0] = 0
    assert validate_market_data(zero_data) == False
    
    # Test with negative prices
    negative_data = valid_data.copy()
    negative_data.iloc[0, 0] = -1
    assert validate_market_data(negative_data) == False 