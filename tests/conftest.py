"""
Shared test fixtures for both unit and integration tests.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-10", freq="B")
    np.random.seed(42)  # For reproducibility

    # Generate sample prices with some trend and volatility
    prices = pd.DataFrame(
        {
            "AAPL": 180 + np.random.normal(0.1, 1.0, len(dates)).cumsum(),
            "MSFT": 390 + np.random.normal(0.2, 1.5, len(dates)).cumsum(),
            "TSLA": 220 + np.random.normal(-0.1, 2.0, len(dates)).cumsum(),
            "META": 370 + np.random.normal(-0.15, 1.8, len(dates)).cumsum(),
        },
        index=dates,
    )

    return prices


@pytest.fixture
def sample_portfolio():
    """Fixture providing sample portfolio positions."""
    return {"AAPL": 1000, "MSFT": 500, "TSLA": -800, "META": -400}


@pytest.fixture
def sample_betas():
    """Fixture providing sample beta values."""
    return {"AAPL": 1.2, "MSFT": 1.1, "TSLA": 1.5, "META": 1.3}


@pytest.fixture
def sample_market_data(sample_price_data):
    """Fixture providing sample market returns data."""
    dates = sample_price_data.index
    np.random.seed(42)
    market_prices = 4800 + np.random.normal(0.05, 1.0, len(dates)).cumsum()
    return pd.Series(market_prices, index=dates).pct_change().fillna(0)


@pytest.fixture
def sample_exchange_rates(sample_price_data):
    """Fixture providing sample USD/CAD exchange rates."""
    dates = sample_price_data.index
    np.random.seed(42)
    base_rate = 1.35
    rates = base_rate + np.random.normal(0, 0.005, len(dates))
    return pd.Series(rates, index=dates)


@pytest.fixture
def mock_yfinance_data():
    """Mock data that would normally come from yfinance."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-10", freq="B")
    np.random.seed(42)

    # Create data for each ticker
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "XOM", "CVX", "COP", "SLB", "EOG", "^GSPC"]
    data = {}

    # Generate data for each ticker and price type
    for ticker in tickers:
        base_price = 100 + np.random.normal(0, 10)  # Different base price for each ticker
        price_series = base_price + np.random.normal(0, 1, len(dates)).cumsum()

        # Add both Close and Adj Close (slightly different values)
        data[(ticker, "Close")] = price_series
        data[(ticker, "Adj Close")] = price_series * (1 + np.random.normal(0, 0.001, len(dates)))

    # Create DataFrame with MultiIndex columns
    df = pd.DataFrame(data, index=dates)
    df.columns = pd.MultiIndex.from_tuples(df.columns, names=["Ticker", "Attribute"])

    return df
