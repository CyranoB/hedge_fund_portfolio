"""
Data acquisition module for the hedge fund portfolio project.
Handles downloading market data and exchange rates.
"""

import pandas as pd
import yfinance as yf
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from datetime import datetime
import calendar
from typing import Tuple, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

def download_market_data(
    tickers: List[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Download historical adjusted close prices for given tickers.
    
    Args:
        tickers (List[str]): List of stock tickers
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: DataFrame with daily adjusted close prices
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[green]Downloading data for {len(tickers)} tickers...",
                total=None
            )
            
            # Download data using yfinance
            df = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                progress=False,
                group_by='column'
            )
            
            progress.update(task, completed=True)
        
        # Extract adjusted close prices
        if len(tickers) == 1:
            prices = df['Close'].to_frame(tickers[0])
        else:
            prices = df['Close']
        
        # Handle missing data
        if prices.isnull().any().any():
            logger.warning("Missing values detected in downloaded data")
            # Forward fill, then backward fill any remaining NAs
            prices = prices.fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"Successfully downloaded data for {len(tickers)} tickers")
        return prices
    
    except Exception as e:
        logger.error(f"Error downloading market data: {str(e)}")
        raise

def get_exchange_rates(
    start_date: str,
    end_date: str,
    simulation: bool = True
) -> pd.Series:
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
            date_range = pd.date_range(start=start_date, end=end_date, freq='B')
            # Use a constant rate for simulation
            SIMULATED_RATE = 1.35  # Example USD/CAD rate
            rates = pd.Series(SIMULATED_RATE, index=date_range, name='USD/CAD')
            logger.info(f"Generated simulated exchange rates using constant rate: {SIMULATED_RATE}")
        else:
            # For real exchange rate data, you would implement API calls here
            # Example: rates = download_exchange_rates_from_api(start_date, end_date)
            raise NotImplementedError("Real exchange rate download not implemented")
        
        return rates
    
    except Exception as e:
        logger.error(f"Error getting exchange rates: {str(e)}")
        raise

def validate_market_data(prices: pd.DataFrame) -> bool:
    """
    Validate the downloaded market data.
    
    Args:
        prices (pd.DataFrame): DataFrame with market prices
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Check for missing values
        if prices.isnull().any().any():
            logger.error("Data contains missing values after cleaning")
            return False
        
        # Check for minimum number of trading days
        min_trading_days = 15  # Assuming we need at least 15 trading days in a month
        if len(prices) < min_trading_days:
            logger.error(f"Insufficient trading days: {len(prices)} < {min_trading_days}")
            return False
        
        # Check for zero or negative prices
        if (prices <= 0).any().any():
            logger.error("Data contains zero or negative prices")
            return False
        
        logger.info("Market data validation passed")
        return True
    
    except Exception as e:
        logger.error(f"Error validating market data: {str(e)}")
        return False
