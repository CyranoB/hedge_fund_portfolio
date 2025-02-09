import os
import numpy as np
import pandas as pd
import pytest
from src.main import run_simulation

def test_run_simulation_success(tmp_path, monkeypatch):
    """
    Test a successful simulation run.
    """
    # Define a test configuration with tickers that will match our mock market data.
    test_config = {
        "tickers_long": ["AAPL", "MSFT"],
        "tickers_short": ["TSLA", "META"],
        "market_index": "^GSPC",
        "initial_capital": 1000000,
        "gross_exposure": 1.5,
        "target_portfolio_beta": 0.0,
        "transaction_fee": 0.001,
        "management_fee": 0.02,
        "analysis_year": 2024,
        "analysis_month": 1
    }
    # Patch load_config so run_simulation uses the test configuration.
    monkeypatch.setattr("src.main.load_config", lambda: test_config)

    # Create dates and build mock market data for each ticker.
    dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="B")
    tickers = test_config["tickers_long"] + test_config["tickers_short"] + [test_config["market_index"]]
    market_data = {}
    for ticker in tickers:
        market_data[ticker] = pd.DataFrame({
            "Adj Close": np.random.randn(len(dates)) + 0.001
        }, index=dates)

    # Instead of returning a dict, combine each ticker's "Adj Close" series into one DataFrame.
    def mock_download(*args, **kwargs):
        combined = pd.DataFrame({ticker: df["Adj Close"] for ticker, df in market_data.items()})
        return combined

    # Create a mock exchange rate series.
    mock_exchange_rates = pd.Series(np.random.randn(len(dates)) + 1.3, index=dates)

    def mock_get_rates(*args, **kwargs):
        return mock_exchange_rates

    def mock_validate(*args, **kwargs):
        return True

    # Patch the key data acquisition functions in the namespace used by run_simulation.
    monkeypatch.setattr("src.main.download_market_data", mock_download)
    monkeypatch.setattr("src.main.get_exchange_rates", mock_get_rates)
    monkeypatch.setattr("src.main.validate_market_data", mock_validate)

    # Patch report generation functions to avoid side effects during tests.
    monkeypatch.setattr("src.reporting.generate_monthly_report", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.reporting.export_to_excel", lambda *args, **kwargs: None)

    # Redirect working directory to a temporary directory.
    os.chdir(tmp_path)

    # Run the simulation.
    results = run_simulation()

    # Basic assertions on simulation output.
    assert isinstance(results, pd.DataFrame)
    assert not results.empty
    for col in ["portfolio_value_usd", "portfolio_value_cad", "portfolio_beta", "daily_return"]:
        assert col in results.columns

    # Verify that a simulation log file was created.
    assert os.path.exists("hedge_fund_simulation.log")


def test_run_simulation_data_error(tmp_path, monkeypatch):
    """
    Test simulation behavior when market data validation fails.
    """
    # Define test configuration
    test_config = {
        "tickers_long": ["AAPL", "MSFT"],
        "tickers_short": ["TSLA", "META"],
        "market_index": "^GSPC",
        "initial_capital": 1000000,
        "gross_exposure": 1.5,
        "target_portfolio_beta": 0.0,
        "transaction_fee": 0.001,
        "management_fee": 0.02,
        "analysis_year": 2024,
        "analysis_month": 1
    }
    monkeypatch.setattr("src.main.load_config", lambda: test_config)

    def mock_validate_error(*args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Market data validation failed")
        return False

    # Patch validate_market_data in the src.main module
    monkeypatch.setattr("src.main.validate_market_data", mock_validate_error)

    # Change to temporary directory
    os.chdir(tmp_path)

    # The simulation should fail with a ValueError when market data is invalid
    with pytest.raises(ValueError) as exc_info:
        run_simulation()

    assert "Market data validation failed" in str(exc_info.value)


def test_run_simulation_report_error(tmp_path, monkeypatch):
    """
    Test simulation behavior when report generation fails.
    """
    # Define test configuration with all required keys
    test_config = {
        "tickers_long": ["AAPL", "MSFT"],
        "tickers_short": ["TSLA", "META"],
        "market_index": "^GSPC",
        "initial_capital": 1000000,
        "gross_exposure": 1.5,
        "target_portfolio_beta": 0.0,
        "transaction_fee": 0.001,
        "management_fee": 0.02,
        "analysis_year": 2024,
        "analysis_month": 1
    }
    
    # Patch load_config to return our test configuration
    monkeypatch.setattr("src.main.load_config", lambda: test_config)

    # For this test we use a flat market data DataFrame to avoid further complications.
    dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="B")
    market_data = pd.DataFrame({
        "AAPL": np.random.randn(len(dates)) + 0.001,
        "MSFT": np.random.randn(len(dates)) + 0.001,
        "TSLA": np.random.randn(len(dates)) + 0.001,
        "META": np.random.randn(len(dates)) + 0.001,
        "^GSPC": np.random.randn(len(dates)) + 0.001
    }, index=dates)

    mock_exchange_rates = pd.Series(np.random.randn(len(dates)) + 1.3, index=dates)

    def mock_download(*args, **kwargs):
        return market_data

    def mock_get_rates(*args, **kwargs):
        return mock_exchange_rates

    def mock_validate(*args, **kwargs):
        return True

    # Patch data acquisition functions in the src.data_acquisition module.
    monkeypatch.setattr("src.data_acquisition.download_market_data", mock_download)
    monkeypatch.setattr("src.data_acquisition.get_exchange_rates", mock_get_rates)
    monkeypatch.setattr("src.data_acquisition.validate_market_data", mock_validate)

    # Patch report generation functions to simulate an error.
    def mock_generate_report_error(*args, **kwargs):
        raise RuntimeError("Failed to generate report")
    def mock_export_error(*args, **kwargs):
        raise RuntimeError("Failed to export data")

    monkeypatch.setattr("src.main.generate_monthly_report", mock_generate_report_error)
    monkeypatch.setattr("src.reporting.export_to_excel", mock_export_error)

    os.chdir(tmp_path)

    # The simulation should propagate the report generation error.
    with pytest.raises(RuntimeError) as exc_info:
        run_simulation()

    assert "Failed to generate report" in str(exc_info.value)

    # Verify that the simulation error was logged.
    assert os.path.exists("hedge_fund_simulation.log")
    with open("hedge_fund_simulation.log", "r") as log_file:
        log_content = log_file.read()
        assert "Error during simulation" in log_content 