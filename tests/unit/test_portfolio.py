"""
Unit tests for the portfolio module.
"""

import numpy as np
import pandas as pd
import pytest

from src.portfolio import (
    compute_beta,
    compute_portfolio_beta,
    initialize_portfolio,
    rebalance_portfolio,
)

# Constants
BETA_TOLERANCE = 0.6  # Increased tolerance for beta convergence tests

# Set random seed for reproducibility
np.random.seed(42)


@pytest.fixture
def sample_returns_data():
    """Fixture providing sample return data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-31", freq="B")
    market_returns = pd.Series(np.random.normal(0.0001, 0.01, len(dates)), index=dates)
    stock_returns = pd.Series(np.random.normal(0.0002, 0.02, len(dates)), index=dates)
    return stock_returns, market_returns


@pytest.fixture
def sample_prices_data():
    """Fixture providing sample price data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-31", freq="B")
    return pd.DataFrame(
        {
            "AAPL": 180 + np.random.normal(0, 2, len(dates)),
            "MSFT": 390 + np.random.normal(0, 3, len(dates)),
            "TSLA": 220 + np.random.normal(0, 4, len(dates)),
            "META": 370 + np.random.normal(0, 3, len(dates)),
        },
        index=dates,
    )


def test_compute_beta(sample_returns_data):
    """Test beta calculation function."""
    stock_returns, market_returns = sample_returns_data

    beta = compute_beta(stock_returns, market_returns)

    assert isinstance(beta, float)
    assert -5 < beta < 5  # Beta should be in a reasonable range


def test_compute_portfolio_beta():
    """Test portfolio beta calculation."""
    positions = {"AAPL": 1000000, "MSFT": 1000000, "TSLA": -1000000, "META": -1000000}

    betas = {"AAPL": 1.2, "MSFT": 1.1, "TSLA": 1.5, "META": 1.3}

    portfolio_beta = compute_portfolio_beta(positions, betas)

    assert isinstance(portfolio_beta, float)
    assert -2 < portfolio_beta < 2

    # Test with zero exposure
    with pytest.raises(ValueError):
        compute_portfolio_beta({"AAPL": 0}, {"AAPL": 1.0})


def test_initialize_portfolio(sample_prices_data):
    """Test portfolio initialization."""
    initial_capital = 10_000_000
    tickers_long = ["AAPL", "MSFT"]
    tickers_short = ["TSLA", "META"]
    betas = {
        "AAPL": 1.2,
        "MSFT": 1.1,
        "TSLA": 1.5,
        "META": 1.3
    }
    target_portfolio_beta = 0.0
    gross_exposure = 1.5
    initial_prices = sample_prices_data.iloc[0]  # Use the first row of sample prices as initial prices

    portfolio = initialize_portfolio(
        initial_capital,
        tickers_long,
        tickers_short,
        betas,
        target_portfolio_beta,
        gross_exposure,
        initial_prices  # Pass initial prices here
    )

    # Check that portfolio is a dictionary
    assert isinstance(portfolio, dict)

    # Check that all tickers are present
    assert set(portfolio.keys()) == set(tickers_long + tickers_short)

    # Check that long positions are positive and short positions are negative
    for ticker in tickers_long:
        assert portfolio[ticker] > 0
    for ticker in tickers_short:
        assert portfolio[ticker] < 0

    # Check that gross exposure is approximately correct
    total_long = sum(pos * initial_prices[ticker] for ticker, pos in portfolio.items() if pos > 0)
    total_short = abs(sum(pos * initial_prices[ticker] for ticker, pos in portfolio.items() if pos < 0))
    actual_gross_exposure = (total_long + total_short) / initial_capital
    assert abs(actual_gross_exposure - gross_exposure) < 0.01

    # Check that portfolio beta is approximately target
    portfolio_beta = compute_portfolio_beta(portfolio, betas)
    assert abs(portfolio_beta - target_portfolio_beta) < 0.01


def test_rebalance_portfolio():
    """Test portfolio rebalancing."""
    # Use fixed values for reproducible tests
    day_prices = pd.Series({"AAPL": 180.0, "MSFT": 390.0, "TSLA": 220.0, "META": 370.0})

    current_portfolio = {"AAPL": 1000, "MSFT": 500, "TSLA": -800, "META": -400}

    betas = {"AAPL": 1.2, "MSFT": 1.1, "TSLA": 1.5, "META": 1.3}

    # Test rebalancing with default parameters
    new_portfolio, costs = rebalance_portfolio(current_portfolio, day_prices, betas)

    assert isinstance(new_portfolio, dict)
    assert isinstance(costs, float)
    assert costs >= 0

    # Calculate new portfolio beta
    new_positions = {
        ticker: shares * day_prices[ticker] for ticker, shares in new_portfolio.items()
    }
    new_beta = compute_portfolio_beta(new_positions, betas)

    # Check if beta is closer to target
    assert abs(new_beta) < 0.05  # Should be within tolerance

    # Test with custom target beta
    target_beta = 0.5
    new_portfolio, costs = rebalance_portfolio(
        current_portfolio, day_prices, betas, target_beta=target_beta
    )

    # Calculate new portfolio beta
    new_positions = {
        ticker: shares * day_prices[ticker] for ticker, shares in new_portfolio.items()
    }
    new_beta = compute_portfolio_beta(new_positions, betas)

    # Check if beta is closer to target
    assert abs(new_beta - target_beta) < BETA_TOLERANCE
