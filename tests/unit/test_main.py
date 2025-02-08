"""
Unit tests for the main application module.
Tests the integration of all components and the main execution workflow.
"""

import pytest
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from src.main import setup_logging, run_simulation
from src.config import load_config

@pytest.fixture
def mock_market_data():
    """Create mock market data for testing."""
    dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq='B')
    data = pd.DataFrame({
        'AAPL': np.random.normal(180, 2, len(dates)),
        'MSFT': np.random.normal(390, 3, len(dates)),
        'TSLA': np.random.normal(220, 4, len(dates)),
        'META': np.random.normal(370, 3, len(dates)),
        '^GSPC': np.random.normal(4800, 10, len(dates))
    }, index=dates)
    return data

@pytest.fixture
def mock_exchange_rates(mock_market_data):
    """Create mock exchange rates for testing."""
    return pd.Series(np.random.normal(1.35, 0.01, len(mock_market_data.index)),
                    index=mock_market_data.index)

def test_setup_logging(tmp_path):
    """Test logging setup function."""
    # Create a temporary log file path
    log_file = tmp_path / "test.log"
    
    # Setup logging
    logger = setup_logging(str(log_file))
    
    # Verify logger is configured correctly
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    
    # Verify log file was created
    assert os.path.exists(log_file)
    
    # Test logging functionality
    test_message = "Test log message"
    logger.info(test_message)
    
    # Verify message was written to file
    with open(log_file) as f:
        log_content = f.read()
        assert test_message in log_content

def test_run_simulation_success(tmp_path, monkeypatch, mock_market_data, mock_exchange_rates):
    """Test successful simulation run."""
    # Mock dependencies
    def mock_download(*args, **kwargs):
        return mock_market_data
    
    def mock_get_rates(*args, **kwargs):
        return mock_exchange_rates
    
    def mock_generate_report(*args, **kwargs):
        pass
    
    def mock_export_excel(*args, **kwargs):
        pass
    
    monkeypatch.setattr('src.data_acquisition.download_market_data', mock_download)
    monkeypatch.setattr('src.data_acquisition.get_exchange_rates', mock_get_rates)
    monkeypatch.setattr('src.reporting.generate_monthly_report', mock_generate_report)
    monkeypatch.setattr('src.reporting.export_to_excel', mock_export_excel)
    
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Run simulation
    results = run_simulation()
    
    # Verify results
    assert isinstance(results, pd.DataFrame)
    assert not results.empty
    assert 'portfolio_value_usd' in results.columns
    assert 'portfolio_value_cad' in results.columns
    assert 'portfolio_beta' in results.columns
    assert 'daily_return' in results.columns
    
    # Verify log file was created
    assert os.path.exists('hedge_fund_simulation.log')
    
    # Check log contents
    with open('hedge_fund_simulation.log') as f:
        log_content = f.read()
        assert "Starting hedge fund portfolio simulation" in log_content
        assert "Simulation completed successfully" in log_content

def test_run_simulation_data_error(tmp_path, monkeypatch):
    """Test simulation handling of data download error."""
    def mock_download_error(*args, **kwargs):
        raise ValueError("Failed to download market data")
    
    monkeypatch.setattr('src.data_acquisition.download_market_data', mock_download_error)
    
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Run simulation and expect error
    with pytest.raises(ValueError) as exc_info:
        run_simulation()
    
    assert "Failed to download market data" in str(exc_info.value)
    
    # Verify error was logged
    assert os.path.exists('hedge_fund_simulation.log')
    with open('hedge_fund_simulation.log') as f:
        log_content = f.read()
        assert "Error during simulation" in log_content

def test_run_simulation_report_error(tmp_path, monkeypatch, mock_market_data, mock_exchange_rates):
    """Test simulation handling of report generation error."""
    # Mock dependencies
    def mock_download(*args, **kwargs):
        return mock_market_data
    
    def mock_get_rates(*args, **kwargs):
        return mock_exchange_rates
    
    def mock_generate_report_error(*args, **kwargs):
        raise RuntimeError("Failed to generate report")
    
    monkeypatch.setattr('src.data_acquisition.download_market_data', mock_download)
    monkeypatch.setattr('src.data_acquisition.get_exchange_rates', mock_get_rates)
    monkeypatch.setattr('src.reporting.generate_monthly_report', mock_generate_report_error)
    
    # Change to temporary directory
    os.chdir(tmp_path)
    
    # Run simulation and expect error
    with pytest.raises(RuntimeError) as exc_info:
        run_simulation()
    
    assert "Failed to generate report" in str(exc_info.value)
    
    # Verify error was logged
    assert os.path.exists('hedge_fund_simulation.log')
    with open('hedge_fund_simulation.log') as f:
        log_content = f.read()
        assert "Error during simulation" in log_content 