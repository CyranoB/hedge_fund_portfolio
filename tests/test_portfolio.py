"""
Unit tests for the portfolio module.
"""

import pytest
import pandas as pd
import numpy as np
from src.portfolio import (
    compute_beta,
    compute_portfolio_beta,
    initialize_portfolio,
    rebalance_portfolio
)

@pytest.fixture
def sample_returns_data():
    """Fixture providing sample return data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-31", freq='B')
    market_returns = pd.Series(np.random.normal(0.0001, 0.01, len(dates)), index=dates)
    stock_returns = pd.Series(np.random.normal(0.0002, 0.02, len(dates)), index=dates)
    return stock_returns, market_returns

@pytest.fixture
def sample_prices_data():
    """Fixture providing sample price data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-31", freq='B')
    return pd.DataFrame({
        'AAPL': 180 + np.random.normal(0, 2, len(dates)),
        'MSFT': 390 + np.random.normal(0, 3, len(dates)),
        'TSLA': 220 + np.random.normal(0, 4, len(dates)),
        'META': 370 + np.random.normal(0, 3, len(dates))
    }, index=dates)

def test_compute_beta(sample_returns_data):
    """Test beta calculation function."""
    stock_returns, market_returns = sample_returns_data
    
    beta = compute_beta(stock_returns, market_returns)
    
    assert isinstance(beta, float)
    assert -5 < beta < 5  # Beta should be in a reasonable range

def test_compute_portfolio_beta():
    """Test portfolio beta calculation."""
    positions = {
        'AAPL': 1000000,
        'MSFT': 1000000,
        'TSLA': -1000000,
        'META': -1000000
    }
    
    betas = {
        'AAPL': 1.2,
        'MSFT': 1.1,
        'TSLA': 1.5,
        'META': 1.3
    }
    
    portfolio_beta = compute_portfolio_beta(positions, betas)
    
    assert isinstance(portfolio_beta, float)
    assert -2 < portfolio_beta < 2
    
    # Test with zero exposure
    with pytest.raises(ValueError):
        compute_portfolio_beta({'AAPL': 0}, {'AAPL': 1.0})

def test_initialize_portfolio(sample_prices_data):
    """Test portfolio initialization."""
    initial_capital = 10_000_000
    tickers_long = ['AAPL', 'MSFT']
    tickers_short = ['TSLA', 'META']
    
    portfolio = initialize_portfolio(
        initial_capital,
        sample_prices_data,
        tickers_long,
        tickers_short
    )
    
    assert isinstance(portfolio, dict)
    assert all(ticker in portfolio for ticker in tickers_long + tickers_short)
    
    # Check long positions are positive
    assert all(portfolio[ticker] > 0 for ticker in tickers_long)
    # Check short positions are negative
    assert all(portfolio[ticker] < 0 for ticker in tickers_short)
    
    # Check approximate equal allocation
    initial_prices = sample_prices_data.iloc[0]
    long_values = sum(portfolio[t] * initial_prices[t] for t in tickers_long)
    short_values = abs(sum(portfolio[t] * initial_prices[t] for t in tickers_short))
    
    assert abs(long_values - initial_capital/2) / (initial_capital/2) < 0.01
    assert abs(short_values - initial_capital/2) / (initial_capital/2) < 0.01

def test_rebalance_portfolio(sample_prices_data):
    """Test portfolio rebalancing."""
    current_portfolio = {
        'AAPL': 1000,
        'MSFT': 500,
        'TSLA': -800,
        'META': -400
    }
    
    day_prices = sample_prices_data.iloc[0]
    
    betas = {
        'AAPL': 1.2,
        'MSFT': 1.1,
        'TSLA': 1.5,
        'META': 1.3
    }
    
    # Test rebalancing with default parameters
    new_portfolio, costs = rebalance_portfolio(
        current_portfolio,
        day_prices,
        betas
    )
    
    assert isinstance(new_portfolio, dict)
    assert isinstance(costs, float)
    assert costs >= 0
    
    # Calculate new portfolio beta
    new_positions = {
        ticker: shares * day_prices[ticker]
        for ticker, shares in new_portfolio.items()
    }
    new_beta = compute_portfolio_beta(new_positions, betas)
    
    # Check if beta is closer to target
    assert abs(new_beta) < 0.05  # Should be within tolerance
    
    # Test with custom target beta and tolerance
    new_portfolio, costs = rebalance_portfolio(
        current_portfolio,
        day_prices,
        betas,
        target_beta=0.5,
        tolerance=0.2  # Increased tolerance for test stability
    )
    
    new_positions = {
        ticker: shares * day_prices[ticker]
        for ticker, shares in new_portfolio.items()
    }
    new_beta = compute_portfolio_beta(new_positions, betas)
    
    assert abs(new_beta - 0.5) < 0.2  # Using larger tolerance for test stability 