"""
Unit tests for the performance module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.performance import calculate_daily_returns, simulate_portfolio
from src.config import MANAGEMENT_FEE_ANNUAL, BETA_TOLERANCE

@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-10", freq='B')
    np.random.seed(42)  # For reproducibility
    
    # Generate sample prices with some trend and volatility
    prices = pd.DataFrame({
        'AAPL': 180 + np.random.normal(0.1, 1.0, len(dates)).cumsum(),
        'MSFT': 390 + np.random.normal(0.2, 1.5, len(dates)).cumsum(),
        'TSLA': 220 + np.random.normal(-0.1, 2.0, len(dates)).cumsum(),
        'META': 370 + np.random.normal(-0.15, 1.8, len(dates)).cumsum()
    }, index=dates)
    
    return prices

@pytest.fixture
def sample_portfolio():
    """Fixture providing sample portfolio positions."""
    return {
        'AAPL': 1000,
        'MSFT': 500,
        'TSLA': -800,
        'META': -400
    }

@pytest.fixture
def sample_betas():
    """Fixture providing sample beta values."""
    return {
        'AAPL': 1.2,
        'MSFT': 1.1,
        'TSLA': 1.5,
        'META': 1.3
    }

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

def test_calculate_daily_returns(sample_price_data):
    """Test daily returns calculation."""
    returns = calculate_daily_returns(sample_price_data)
    
    assert isinstance(returns, pd.DataFrame)
    assert returns.index.equals(sample_price_data.index)
    assert returns.columns.equals(sample_price_data.columns)
    assert not returns.isnull().any().any()
    
    # First day should be 0 (or NaN filled with 0)
    assert all(returns.iloc[0] == 0)
    
    # Manual verification of return calculation
    for col in returns.columns:
        for i in range(1, len(returns)):
            expected_return = (
                sample_price_data[col].iloc[i] - sample_price_data[col].iloc[i-1]
            ) / sample_price_data[col].iloc[i-1]
            assert np.isclose(returns[col].iloc[i], expected_return)

def test_simulate_portfolio(
    sample_price_data,
    sample_portfolio,
    sample_betas,
    sample_market_data,
    sample_exchange_rates
):
    """Test portfolio simulation."""
    results = simulate_portfolio(
        sample_price_data,
        sample_portfolio,
        sample_betas,
        sample_exchange_rates,
        0.02,  # Add management fee parameter
        target_beta=0  # Add target beta parameter
    )
    
    assert isinstance(results, pd.DataFrame)
    assert len(results) == len(sample_price_data)
    
    # Check required columns exist
    required_columns = [
        'portfolio_value_usd',
        'portfolio_value_cad',
        'portfolio_beta',
        'daily_return',
        'management_fee',
        'transaction_costs',
        'rebalanced',
        'exchange_rate'
    ]
    assert all(col in results.columns for col in required_columns)
    
    # Check data types and value ranges
    assert results['portfolio_value_usd'].dtype == float
    assert results['portfolio_value_cad'].dtype == float
    assert results['portfolio_beta'].dtype == float
    assert results['daily_return'].dtype == float
    assert results['management_fee'].dtype == float
    assert results['transaction_costs'].dtype == float
    assert results['rebalanced'].dtype == bool
    assert results['exchange_rate'].dtype == float
    
    # Verify all values are non-negative where appropriate
    assert all(results['portfolio_value_usd'] > 0)
    assert all(results['portfolio_value_cad'] > 0)
    assert all(results['management_fee'] >= 0)
    assert all(results['transaction_costs'] >= 0)
    assert all(results['exchange_rate'] > 0)
    
    # Verify management fee calculation
    expected_daily_fee = MANAGEMENT_FEE_ANNUAL / 252
    for value_usd, fee in zip(results['portfolio_value_usd'], results['management_fee']):
        assert np.isclose(fee, value_usd * expected_daily_fee)
    
    # Verify CAD conversion
    for usd, cad, rate in zip(
        results['portfolio_value_usd'],
        results['portfolio_value_cad'],
        results['exchange_rate']
    ):
        assert np.isclose(cad, usd * rate)
    
    # Verify rebalancing triggers
    for beta, rebalanced in zip(results['portfolio_beta'], results['rebalanced']):
        if abs(beta) > BETA_TOLERANCE:
            assert rebalanced
    
    # Verify daily returns calculation
    for i in range(1, len(results)):
        expected_return = (
            results['portfolio_value_usd'].iloc[i] -
            results['portfolio_value_usd'].iloc[i-1]
        ) / results['portfolio_value_usd'].iloc[i-1]
        assert np.isclose(results['daily_return'].iloc[i], expected_return)

def test_simulate_portfolio_with_target_beta(
    sample_price_data,
    sample_portfolio,
    sample_betas,
    sample_market_data,
    sample_exchange_rates
):
    """Test portfolio simulation with non-zero target beta."""
    target_beta = 0.5
    results = simulate_portfolio(
        sample_price_data,
        sample_portfolio,
        sample_betas,
        sample_market_data,
        sample_exchange_rates,
        target_beta=target_beta
    )
    
    # Verify beta convergence
    final_beta = results['portfolio_beta'].iloc[-1]
    assert abs(final_beta - target_beta) <= BETA_TOLERANCE * 1.5  # Allow some margin
    
    # Check that rebalancing occurs when beta deviates
    assert results['rebalanced'].any()
    for beta, rebalanced in zip(results['portfolio_beta'], results['rebalanced']):
        if abs(beta - target_beta) > BETA_TOLERANCE:
            assert rebalanced 