"""
Unit tests for the configuration module.
"""

from src import config

def test_initial_capital():
    """Test that initial capital is set correctly."""
    assert config.INITIAL_CAPITAL_USD == 10_000_000
    assert isinstance(config.INITIAL_CAPITAL_USD, int)

def test_gross_exposure():
    """Test that gross exposure is set correctly."""
    assert config.GROSS_EXPOSURE == 10_000_000
    assert isinstance(config.GROSS_EXPOSURE, int)

def test_ticker_lists():
    """Test that ticker lists are properly defined."""
    # Test long tickers
    assert isinstance(config.LONG_TICKERS, list)
    assert len(config.LONG_TICKERS) == 5
    assert all(isinstance(ticker, str) for ticker in config.LONG_TICKERS)
    
    # Test short tickers
    assert isinstance(config.SHORT_TICKERS, list)
    assert len(config.SHORT_TICKERS) == 5
    assert all(isinstance(ticker, str) for ticker in config.SHORT_TICKERS)
    
    # Test market index
    assert isinstance(config.MARKET_INDEX, str)
    assert config.MARKET_INDEX == '^GSPC'

def test_fee_parameters():
    """Test that fee parameters are set correctly."""
    assert config.MANAGEMENT_FEE_ANNUAL == 0.02
    assert isinstance(config.MANAGEMENT_FEE_ANNUAL, float)
    assert 0 < config.MANAGEMENT_FEE_ANNUAL < 1
    
    assert config.TRANSACTION_FEE_PER_SHARE == 0.01
    assert isinstance(config.TRANSACTION_FEE_PER_SHARE, float)
    assert config.TRANSACTION_FEE_PER_SHARE > 0

def test_analysis_parameters():
    """Test that analysis parameters are set correctly."""
    assert config.ANALYSIS_YEAR == 2025
    assert isinstance(config.ANALYSIS_YEAR, int)
    
    assert config.ANALYSIS_MONTH == 1
    assert isinstance(config.ANALYSIS_MONTH, int)
    assert 1 <= config.ANALYSIS_MONTH <= 12
    
    assert config.BETA_TOLERANCE == 0.05
    assert isinstance(config.BETA_TOLERANCE, float)
    assert 0 < config.BETA_TOLERANCE < 1 