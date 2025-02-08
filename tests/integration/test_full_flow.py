"""
Integration tests for the complete hedge fund portfolio workflow.
Tests the end-to-end functionality of the application with real data.
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.config import load_config
from src.main import run_simulation

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def test_full_workflow(tmp_path):
    """
    Test the complete workflow of the hedge fund portfolio application.
    This test runs the actual simulation with real data but for a shorter period.
    """
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
    assert os.path.exists("docs/monthly_report.pdf")
    assert os.path.exists("docs/portfolio_performance.xlsx")
    assert os.path.exists("hedge_fund_simulation.log")

    # Check log file contents
    with open("hedge_fund_simulation.log", "r") as f:
        log_content = f.read()
        assert "Starting hedge fund portfolio simulation" in log_content
        assert "Downloading market data" in log_content
        assert "Simulation completed successfully" in log_content

    # Verify Excel file contents
    excel_data = pd.read_excel("docs/portfolio_performance.xlsx", sheet_name=None)
    assert "Daily Performance" in excel_data
    assert "Rebalancing Events" in excel_data
    assert "Summary Statistics" in excel_data

    # Check portfolio values
    assert all(results["portfolio_value_usd"] > 0)
    assert all(results["portfolio_value_cad"] > 0)
    assert all(results["exchange_rate"] > 0)

    # Verify beta is being controlled
    config = load_config()
    beta_tolerance = config.get("beta_tolerance", 0.05)
    assert abs(results["portfolio_beta"].mean()) < beta_tolerance * 2  # Allow some margin


def test_error_recovery(tmp_path):
    """
    Test the application's ability to handle and recover from errors during execution.
    """
    # Change to temporary directory
    os.chdir(tmp_path)

    # Create an invalid directory structure to test error handling
    os.makedirs("docs", exist_ok=True)
    with open("docs/monthly_report.pdf", "w") as f:
        f.write("invalid pdf")  # Create an invalid PDF file

    try:
        run_simulation()
    except Exception as e:
        # Verify error was logged
        assert os.path.exists("hedge_fund_simulation.log")
        with open("hedge_fund_simulation.log", "r") as f:
            log_content = f.read()
            assert "Error during simulation" in log_content

        # Check that temporary files were cleaned up
        assert not os.path.exists("docs/portfolio_performance.xlsx.tmp")
