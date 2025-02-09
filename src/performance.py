"""
Performance module for the hedge fund portfolio project.
Handles daily returns calculation and portfolio performance simulation.
"""

import logging
from typing import Dict, Union, Tuple, List

import pandas as pd
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
import numpy as np

from .config import BETA_TOLERANCE
from .portfolio import compute_portfolio_beta, rebalance_portfolio, initialize_portfolio

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


def calculate_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily returns from adjusted close prices.

    Args:
        prices (pd.DataFrame): DataFrame with daily prices for each ticker

    Returns:
        pd.DataFrame: DataFrame with daily returns
    """
    try:
        # Calculate percentage returns
        returns = prices.pct_change()

        # Handle any missing data
        if returns.isnull().any().any():
            logger.warning("Missing values detected in returns calculation")
            returns = returns.fillna(0)  # Replace NaN with 0 for first day

        logger.debug("Daily returns calculated successfully")
        return returns

    except Exception as e:
        logger.error(f"Error calculating daily returns: {str(e)}")
        raise


def simulate_portfolio(price_data: pd.DataFrame,
                       portfolio: dict,
                       betas: dict,
                       exchange_rates: pd.Series,
                       management_fee_rate: float,
                       target_beta: float) -> Tuple[pd.DataFrame, List[Dict[str, float]]]:
    """
    Simulate portfolio performance over the given price data.
    
    Args:
        price_data (pd.DataFrame): Daily price data for all tickers.
        portfolio (dict): Dictionary of ticker positions (shares).
        betas (dict): Dictionary of beta values per ticker.
        exchange_rates (pd.Series): Daily exchange rates.
        management_fee_rate (float): Annual management fee rate.
        target_beta (float): Target portfolio beta.
    
    Returns:
        Tuple[pd.DataFrame, List[Dict[str, float]]]: DataFrame with simulation results and list of transaction logs
    """
    # Initialize results storage
    results = []
    all_transaction_logs = []  # Store all transaction logs
    current_portfolio = portfolio.copy()
    
    # Calculate initial portfolio value and gross exposure
    initial_prices = price_data.iloc[0]
    initial_positions = {ticker: shares * initial_prices[ticker] 
                        for ticker, shares in current_portfolio.items()}
    initial_portfolio_value = sum(initial_positions.values())
    initial_gross_exposure = sum(abs(value) for value in initial_positions.values())
    
    # Log initial portfolio state
    logger.info(f"Initial portfolio net value: ${initial_portfolio_value:,.2f}")
    logger.info(f"Initial portfolio gross exposure: ${initial_gross_exposure:,.2f}")
    logger.info("Initial positions:")
    for ticker, value in initial_positions.items():
        logger.info(f"  {ticker}: {current_portfolio[ticker]:,.0f} shares, ${value:,.2f}")
    
    # Iterate through each day
    for date in price_data.index:
        # Get current day's prices
        current_prices = price_data.loc[date]
        
        # Calculate portfolio values and positions
        positions = {ticker: shares * current_prices[ticker] 
                    for ticker, shares in current_portfolio.items()}
        portfolio_value_usd = sum(positions.values())
        gross_exposure_usd = sum(abs(value) for value in positions.values())
        
        # Log if gross exposure changes significantly
        if len(results) > 0:
            prev_exposure = sum(abs(value) for value in 
                              {t: s * price_data.loc[price_data.index[price_data.index.get_loc(date)-1]][t] 
                               for t, s in current_portfolio.items()}.values())
            if abs((gross_exposure_usd - prev_exposure) / prev_exposure) > 0.05:  # 5% change
                logger.info(f"Significant exposure change on {date}: ${gross_exposure_usd:,.2f} (prev: ${prev_exposure:,.2f})")
        
        # Calculate current portfolio beta
        current_beta = compute_portfolio_beta(positions, betas)
        
        # Check if rebalancing is needed
        needs_rebalancing = abs(current_beta - target_beta) > BETA_TOLERANCE
        transaction_cost = 0.0
        
        # Perform rebalancing if needed
        if needs_rebalancing:
            # Pass the current prices and date
            current_portfolio, rebalance_cost, transaction_logs = rebalance_portfolio(
                current_portfolio,
                current_prices,
                betas,
                target_beta,
                date  # Pass the date directly
            )
            transaction_cost = rebalance_cost
            all_transaction_logs.extend(transaction_logs)  # Add new transaction logs
            
            # Log portfolio state after rebalancing
            new_positions = {ticker: shares * current_prices[ticker] 
                           for ticker, shares in current_portfolio.items()}
            new_gross_exposure = sum(abs(value) for value in new_positions.values())
            logger.info(f"Gross exposure after rebalancing: ${new_gross_exposure:,.2f}")
        
        # Calculate daily return based on gross exposure
        if len(results) > 0:
            prev_gross_exposure = sum(abs(value) for value in 
                                    {t: s * price_data.loc[price_data.index[price_data.index.get_loc(date)-1]][t] 
                                     for t, s in current_portfolio.items()}.values())
            daily_return = (gross_exposure_usd / prev_gross_exposure) - 1 if prev_gross_exposure > 0 else 0.0
        else:
            daily_return = 0.0  # First day has no return
        
        # Calculate management fee based on gross exposure
        management_fee = gross_exposure_usd * (management_fee_rate / 252)
        
        # Store daily results
        results.append({
            "portfolio_value_usd": portfolio_value_usd,
            "gross_exposure_usd": gross_exposure_usd,
            "portfolio_value_cad": portfolio_value_usd * exchange_rates[date],
            "portfolio_beta": current_beta,
            "daily_return": daily_return,
            "management_fee": management_fee,
            "transaction_costs": transaction_cost,
            "rebalanced": needs_rebalancing,
            "exchange_rate": exchange_rates[date]
        })
    
    # Log final portfolio state
    final_gross_exposure = results[-1]["gross_exposure_usd"]
    logger.info(f"Final portfolio net value: ${results[-1]['portfolio_value_usd']:,.2f}")
    logger.info(f"Final portfolio gross exposure: ${final_gross_exposure:,.2f}")
    
    # Convert results to DataFrame
    return pd.DataFrame(results, index=price_data.index), all_transaction_logs


def compute_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate beta coefficient using covariance method.

    Args:
        stock_returns (pd.Series): Daily returns for a stock
        market_returns (pd.Series): Daily returns for the market index

    Returns:
        float: Beta coefficient
    """
    try:
        # Calculate beta using covariance method
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        beta = covariance / market_variance if market_variance != 0 else 0

        return beta

    except Exception as e:
        logger.error(f"Error computing beta: {str(e)}")
        raise
