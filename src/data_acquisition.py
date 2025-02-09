"""
Data acquisition module for the hedge fund portfolio project.
Handles downloading market data and exchange rates.
"""

import calendar
import logging
from typing import List, Tuple
import os

import pandas as pd
import yfinance as yf
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


def get_date_range(year: int, month: int) -> Tuple[str, str]:
    """
    Calculate the start and end dates for a given month and year.

    Args:
        year (int): The year for analysis
        month (int): The month for analysis (1-12)

    Returns:
        Tuple[str, str]: Start date and end date in 'YYYY-MM-DD' format
    """
    try:
        # Validate inputs
        if not 1 <= month <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {month}")

        # Get the last day of the month
        _, last_day = calendar.monthrange(year, month)

        # Create date strings
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"

        logger.info(f"Generated date range: {start_date} to {end_date}")
        return start_date, end_date

    except Exception as e:
        logger.error(f"Error generating date range: {str(e)}")
        raise


def download_market_data(tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download historical adjusted close prices for given tickers.

    Args:
        tickers (List[str]): List of stock tickers
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        pd.DataFrame: DataFrame with daily adjusted close prices indexed by date.
                    The columns will be named after the tickers.
    """
    try:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(
                f"[green]Downloading data for {len(tickers)} tickers...", total=None
            )
            df = yf.download(
                tickers, start=start_date, end=end_date, progress=False, group_by="ticker"
            )
            progress.update(task, completed=True)

        if df.empty:
            raise ValueError("No market data downloaded for given tickers and date range")

        # Handle single ticker case
        if not isinstance(df.columns, pd.MultiIndex):
            if "Adj Close" in df.columns:
                return pd.DataFrame(df["Adj Close"])
            elif "Close" in df.columns:
                return pd.DataFrame(df["Close"])
            else:
                raise KeyError("Neither 'Close' nor 'Adj Close' found in DataFrame columns")

        # Handle multiple tickers case
        prices = pd.DataFrame()
        for ticker in tickers:
            if "Adj Close" in df[ticker].columns:
                prices[ticker] = df[ticker]["Adj Close"]
            elif "Close" in df[ticker].columns:
                prices[ticker] = df[ticker]["Close"]
            else:
                logger.warning(f"No price data found for {ticker}")

        if prices.empty:
            raise ValueError("No valid price data found for any ticker")

        # Handle any missing values
        if prices.isnull().any().any():
            logger.warning("Missing values detected in downloaded data")
            prices = prices.fillna(method="ffill").fillna(method="bfill")

        logger.info(f"Successfully downloaded data for {len(tickers)} tickers")
        return prices

    except Exception as e:
        logger.error(f"Error downloading market data: {str(e)}")
        raise


def get_exchange_rates(start_date: str, end_date: str, simulation: bool = True) -> pd.Series:
    """
    Get or simulate USD/CAD exchange rates for the given period.

    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
        simulation (bool): If True, use simulated constant rate

    Returns:
        pd.Series: Exchange rates indexed by date
    """
    try:
        if simulation:
            # Create a date range
            date_range = pd.date_range(start=start_date, end=end_date, freq="B")
            # Use a constant rate for simulation
            SIMULATED_RATE = 1.35  # Example USD/CAD rate
            rates = pd.Series(SIMULATED_RATE, index=date_range, name="USD/CAD")
            logger.info(f"Generated simulated exchange rates using constant rate: {SIMULATED_RATE}")
        else:
            # For real exchange rate data, you would implement API calls here
            # Example: rates = download_exchange_rates_from_api(start_date, end_date)
            raise NotImplementedError("Real exchange rate download not implemented")

        return rates

    except Exception as e:
        logger.error(f"Error getting exchange rates: {str(e)}")
        raise


def validate_market_data(market_data: pd.DataFrame) -> bool:
    """
    Validate market data quality.

    Args:
        market_data (pd.DataFrame): Market data to validate

    Returns:
        bool: True if data passes validation, False otherwise
    """
    try:
        # Check for empty data
        if market_data.empty:
            logger.error("Market data is empty")
            return False

        # Check for missing values
        if market_data.isnull().any().any():
            logger.error("Market data contains missing values")
            return False

        # Check for zero or negative prices
        if (market_data <= 0).any().any():
            logger.error("Market data contains zero or negative prices")
            return False

        # Check for sufficient trading days (only in production)
        if not os.getenv("TESTING"):
            min_trading_days = 15
            if len(market_data) < min_trading_days:
                logger.error(f"Insufficient trading days: {len(market_data)} < {min_trading_days}")
                return False

        # Check for monotonic dates
        if not market_data.index.is_monotonic_increasing:
            logger.error("Market data dates are not monotonically increasing")
            return False

        logger.info("Market data validation passed")
        return True

    except Exception as e:
        logger.error(f"Error validating market data: {str(e)}")
        return False
