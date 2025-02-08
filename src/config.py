"""
Configuration module for the hedge fund portfolio project.
Contains all global parameters and settings used throughout the application.
"""

# Portfolio Parameters
INITIAL_CAPITAL_USD = 10_000_000
GROSS_EXPOSURE = 10_000_000

# Ticker Lists
LONG_TICKERS = ['AAPL', 'MSFT', 'AMZN', 'JNJ', 'WMT']
SHORT_TICKERS = ['TSLA', 'META', 'SHOP', 'NVDA', 'BA']
MARKET_INDEX = '^GSPC'

# Fee Parameters
MANAGEMENT_FEE_ANNUAL = 0.02  # 2% per year
TRANSACTION_FEE_PER_SHARE = 0.01

# Analysis Period and Rebalancing Settings
ANALYSIS_YEAR = 2025
ANALYSIS_MONTH = 1  # January
BETA_TOLERANCE = 0.05
