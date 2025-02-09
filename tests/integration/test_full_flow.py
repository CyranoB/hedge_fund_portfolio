"""
Integration tests for the complete hedge fund portfolio workflow.
Tests the end-to-end functionality of the application with real data.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

from src.config import load_config
from src.main import run_simulation

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def test_config(monkeypatch):
    """Fixture to provide test configuration."""
    config = {
        "tickers_long": ["AAPL", "MSFT"],
        "tickers_short": ["TSLA", "META"],
        "market_index": "^GSPC",
        "initial_capital": 1000000,
        "gross_exposure": 1.5,
        "target_portfolio_beta": 0.0,
        "transaction_fee": 0.001,
        "financing_fee": 0.02,
        "analysis_year": 2024,
        "analysis_month": 1
    }
    monkeypatch.setattr("src.main.load_config", lambda: config)
    return config


def test_full_workflow(tmp_path, test_config):
    """
    Test the complete workflow of the hedge fund portfolio application.
    This test runs the actual simulation with real data but for a shorter period.
    """
    # Create necessary directories
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to temporary directory for test outputs
    os.chdir(tmp_path)

    # Run the simulation
    results = run_simulation()

    # Verify simulation results
    assert isinstance(results, pd.DataFrame)
    assert not results.empty

    # Check all required columns are present
    required_columns = [
        "portfolio_value_usd",
        "portfolio_value_cad",
        "portfolio_beta",
        "daily_return",
        "management_fee",
        "transaction_costs",
        "rebalanced",
        "exchange_rate",
    ]
    assert all(col in results.columns for col in required_columns)

    # Verify output files were generated
    assert os.path.exists("hedge_fund_simulation.log")

    # Check log file contents
    with open("hedge_fund_simulation.log", "r") as f:
        log_content = f.read()
        assert "Starting hedge fund portfolio simulation" in log_content
        assert "Downloading market data" in log_content
        assert "Simulation completed successfully" in log_content


def test_error_recovery(tmp_path, monkeypatch):
    """Test that the application can handle and recover from errors."""
    # Create a configuration with invalid tickers
    invalid_config = {
        "tickers_long": ["INVALID1", "INVALID2"],
        "tickers_short": ["INVALID3", "INVALID4"],
        "market_index": "^INVALID",
        "initial_capital": 1000000,
        "gross_exposure": 1.5,
        "target_portfolio_beta": 0.0,
        "transaction_fee": 0.001,
        "financing_fee": 0.02,
        "analysis_year": 2024,
        "analysis_month": 1
    }
    monkeypatch.setattr("src.main.load_config", lambda: invalid_config)

    # Change to temporary directory
    os.chdir(tmp_path)

    # The simulation should fail when trying to download data for invalid tickers
    with pytest.raises(Exception) as exc_info:
        run_simulation()

    # Verify that the error was logged
    assert os.path.exists("hedge_fund_simulation.log")
    with open("hedge_fund_simulation.log", "r") as f:
        log_content = f.read()
        assert any(["Error" in line and "market data" in line for line in log_content.splitlines()])
