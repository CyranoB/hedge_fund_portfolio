"""
Integration tests for the complete hedge fund portfolio simulation workflow.
These tests verify the end-to-end functionality of the simulation process,
including configuration loading, data acquisition, portfolio management,
and report generation. While located in the unit tests directory, these tests
use extensive mocking to test component integration without external dependencies.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from rich.logging import RichHandler
from src.main import run_simulation
from src.config import (
    ANALYSIS_YEAR,
    ANALYSIS_MONTH,
    LONG_TICKERS,
    SHORT_TICKERS,
    MARKET_INDEX
)

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True),
            logging.FileHandler("hedge_fund_simulation.log", mode="w")
        ]
    )

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = {
        "tickers_long": ["AAPL", "GOOGL"],
        "tickers_short": ["MSFT"],
        "market_index": "^GSPC",
        "tickers": ["AAPL", "GOOGL", "MSFT", "^GSPC"],
        "initial_capital": 1000000,
        "management_fee": 0.02,
        "target_beta": 0.8
    }
    return config

@pytest.fixture
def mock_yf_download(mock_yfinance_data):
    """Mock yfinance download function."""
    def _mock(*args, **kwargs):
        return mock_yfinance_data
    return _mock

@pytest.fixture
def mock_exchange_rates(sample_exchange_rates):
    """Mock exchange rates function."""
    def _mock(*args, **kwargs):
        return sample_exchange_rates
    return _mock

@pytest.fixture
def mock_daily_returns(sample_price_data):
    """Mock daily returns calculation."""
    def _mock(*args, **kwargs):
        return sample_price_data.pct_change().fillna(0)
    return _mock

@pytest.fixture
def mock_betas():
    """Mock beta values."""
    return {
        'AAPL': 1.2,
        'GOOGL': 1.1,
        'MSFT': 1.3,
        '^GSPC': 1.0
    }

@pytest.fixture
def mock_simulate_portfolio(mock_betas):
    """Mock portfolio simulation."""
    def _mock(*args, **kwargs):
        dates = pd.date_range(start='2025-01-01', end='2025-01-10', freq='B')
        return pd.DataFrame({
            'portfolio_value_usd': np.random.normal(1000000, 50000, len(dates)),
            'portfolio_value_cad': np.random.normal(1300000, 65000, len(dates)),
            'portfolio_beta': np.random.normal(0, 0.1, len(dates)),
            'daily_return': np.random.normal(0.0001, 0.02, len(dates)),
            'management_fee': np.random.uniform(500, 1000, len(dates)),
            'transaction_costs': np.random.uniform(0, 2000, len(dates)),
            'rebalanced': np.random.choice([True, False], len(dates), p=[0.2, 0.8]),
            'exchange_rate': np.random.normal(1.35, 0.005, len(dates))
        }, index=dates)
    return _mock

@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch, mock_config, mock_yf_download, mock_betas,
                mock_exchange_rates, mock_daily_returns, mock_simulate_portfolio):
    """Set up all mocks for testing."""
    monkeypatch.setattr('src.config.load_config', lambda: mock_config)
    monkeypatch.setattr('yfinance.download', mock_yf_download)
    monkeypatch.setattr('src.data_acquisition.get_exchange_rates', mock_exchange_rates)
    monkeypatch.setattr('src.performance.calculate_daily_returns', mock_daily_returns)
    monkeypatch.setattr('src.performance.simulate_portfolio', mock_simulate_portfolio)
    monkeypatch.setattr('src.portfolio.compute_beta', lambda *args: mock_betas.get(args[0], 1.0))
    # Mock report generation to avoid file operations
    monkeypatch.setattr('src.reporting.generate_monthly_report', lambda *args, **kwargs: None)
    monkeypatch.setattr('src.reporting.export_to_excel', lambda *args, **kwargs: None)

def test_run_simulation(tmp_path):
    """Test the complete simulation workflow."""
    # Redirect output to temp directory
    os.chdir(tmp_path)
    
    # Run simulation
    results = run_simulation()
    
    # Verify the results
    assert isinstance(results, pd.DataFrame)
    assert not results.empty
    assert 'portfolio_value_usd' in results.columns
    assert 'portfolio_value_cad' in results.columns
    assert 'portfolio_beta' in results.columns
    
    # Verify log file was created
    assert os.path.exists('hedge_fund_simulation.log')
    with open('hedge_fund_simulation.log', 'r') as f:
        log_content = f.read()
        assert "Starting hedge fund portfolio simulation..." in log_content
        assert "Simulation completed successfully" in log_content

def test_run_simulation_error_handling(tmp_path, monkeypatch):
    """Test error handling in the simulation workflow."""
    def mock_download_error(*args, **kwargs):
        raise ValueError("Mock download error")
    
    monkeypatch.setattr('yfinance.download', mock_download_error)
    
    # Redirect output to temp directory
    os.chdir(tmp_path)
    
    # Run simulation and check for error handling
    with pytest.raises(ValueError) as exc_info:
        run_simulation()
    
    assert str(exc_info.value) == "Mock download error"
    
    # Verify error was logged
    assert os.path.exists('hedge_fund_simulation.log')
    with open('hedge_fund_simulation.log', 'r') as f:
        log_content = f.read()
        assert "Error during simulation: Mock download error" in log_content 