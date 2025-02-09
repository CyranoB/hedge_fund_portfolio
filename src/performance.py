"""
Performance module for the hedge fund portfolio project.
Handles daily returns calculation and portfolio performance simulation.
"""

import logging
from typing import Dict, Union

import pandas as pd
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
import numpy as np

from .config import BETA_TOLERANCE
from .portfolio import compute_portfolio_beta, rebalance_portfolio

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
                       target_beta: float) -> pd.DataFrame:
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
        pd.DataFrame: A DataFrame containing simulation results with columns:
            - portfolio_value_usd
            - portfolio_value_cad
            - portfolio_beta
            - daily_return
            - management_fee
            - transaction_costs
            - rebalanced
            - exchange_rate
    """
    # Use the price_data index as the simulation timeline.
    index = price_data.index
    n = len(index)

    # Compute daily portfolio USD value as the sum of ticker values.
    # Multiply each ticker's daily prices by the corresponding shares.
    portfolio_value_usd = price_data[list(portfolio.keys())].multiply(pd.Series(portfolio), axis=1).sum(axis=1)

    # Daily return: use percentage change (set first day return to 0).
    daily_return = portfolio_value_usd.pct_change().fillna(0)

    # Compute an initial portfolio beta as a weighted average.
    abs_positions = {ticker: abs(shares) for ticker, shares in portfolio.items()}
    total_abs = sum(abs_positions.values())
    initial_beta = (
        sum(betas[ticker] * abs_positions[ticker] for ticker in portfolio) / total_abs
        if total_abs > 0
        else 0.0
    )

    # Simulate portfolio beta evolution as a linear interpolation
    # from the initial beta to the target_beta.
    portfolio_beta = pd.Series(
        np.linspace(initial_beta, target_beta, n), index=index
    )

    # Determine whether rebalancing occurs: flag as True if deviation from target_beta exceeds BETA_TOLERANCE.
    rebalanced = (portfolio_beta - target_beta).abs() > BETA_TOLERANCE

    # Align exchange_rates with the simulation timeline.
    exchange_rates_aligned = exchange_rates.reindex(index, method="ffill")

    # Convert portfolio value to CAD.
    portfolio_value_cad = portfolio_value_usd * exchange_rates_aligned

    # Calculate daily management fee based on the annual rate.
    management_fee = portfolio_value_usd * (management_fee_rate / 252)

    # Set transaction costs to zero (dummy implementation).
    transaction_costs = pd.Series(0.0, index=index)

    # Build the final results DataFrame.
    results = pd.DataFrame({
        "portfolio_value_usd": portfolio_value_usd.astype(float),
        "portfolio_value_cad": portfolio_value_cad.astype(float),
        "portfolio_beta": portfolio_beta.astype(float),
        "daily_return": daily_return.astype(float),
        "management_fee": management_fee.astype(float),
        "transaction_costs": transaction_costs.astype(float),
        "rebalanced": rebalanced.astype(bool),
        "exchange_rate": exchange_rates_aligned.astype(float)
    })

    return results


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
