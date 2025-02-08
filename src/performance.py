"""
Performance module for the hedge fund portfolio project.
Handles daily returns calculation and portfolio performance simulation.
"""

import logging
from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from src.config import BETA_TOLERANCE, MANAGEMENT_FEE_ANNUAL
from src.portfolio import compute_portfolio_beta, rebalance_portfolio

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


def simulate_portfolio(
    daily_prices: pd.DataFrame,
    portfolio: Dict[str, float],
    daily_returns: Union[pd.DataFrame, Dict[str, float]],
    exchange_rates: pd.Series,
    management_fee: Union[float, pd.Series],
    target_beta: float = 0,
) -> pd.DataFrame:
    """
    Simulate daily portfolio performance with rebalancing and fee calculations.

    Args:
        daily_prices (pd.DataFrame): Daily prices for all tickers
        portfolio (Dict[str, float]): Initial portfolio positions
        daily_returns (Union[pd.DataFrame, Dict[str, float]]): Daily returns for each ticker
        exchange_rates (pd.Series): Daily USD/CAD exchange rates
        management_fee (Union[float, pd.Series]): Annual management fee rate or series
        target_beta (float): Target portfolio beta

    Returns:
        pd.DataFrame: Daily simulation results
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[green]Simulating portfolio performance...", total=len(daily_prices)
            )

            # Initialize results storage
            results = []
            current_portfolio = portfolio.copy()

            # Convert daily_returns to DataFrame if it's a dictionary
            if isinstance(daily_returns, dict):
                betas = daily_returns
            else:
                # Calculate betas for each ticker using the entire period
                # Find the market index column (either '^GSPC' or the last column)
                market_col = (
                    "^GSPC" if "^GSPC" in daily_returns.columns else daily_returns.columns[-1]
                )
                market_returns = daily_returns[market_col]
                betas = {}
                for ticker in daily_returns.columns:
                    if ticker != market_col:
                        stock_returns = daily_returns[ticker]
                        betas[ticker] = compute_beta(stock_returns, market_returns)

            # Convert management_fee to float if it's a Series
            if isinstance(management_fee, pd.Series):
                management_fee = management_fee.iloc[0]

            # Simulate each day
            for date, prices in daily_prices.iterrows():
                # Calculate current position values and portfolio metrics
                positions = {
                    ticker: shares * prices[ticker] for ticker, shares in current_portfolio.items()
                }

                portfolio_value_usd = abs(
                    sum(positions.values())
                )  # Use absolute value for total portfolio value
                portfolio_beta = compute_portfolio_beta(positions, betas)

                # Check if rebalancing is needed
                rebalanced = False
                transaction_costs = 0.0
                if abs(portfolio_beta - target_beta) > BETA_TOLERANCE:
                    current_portfolio, transaction_costs = rebalance_portfolio(
                        current_portfolio, prices, betas, target_beta=target_beta
                    )
                    rebalanced = True

                # Calculate daily management fee
                daily_fee = (management_fee / 252) * portfolio_value_usd

                # Convert to CAD
                portfolio_value_cad = portfolio_value_usd * exchange_rates[date]

                # Calculate daily return (before fees and transaction costs)
                if len(results) > 0:
                    previous_value = results[-1]["portfolio_value_usd"]
                    daily_return = (portfolio_value_usd - previous_value) / previous_value
                else:
                    daily_return = 0.0

                # Store daily results
                results.append(
                    {
                        "date": date,
                        "portfolio_value_usd": portfolio_value_usd,
                        "portfolio_value_cad": portfolio_value_cad,
                        "portfolio_beta": portfolio_beta,
                        "daily_return": daily_return,
                        "management_fee": daily_fee,
                        "transaction_costs": transaction_costs,
                        "rebalanced": rebalanced,
                        "exchange_rate": exchange_rates[date],
                    }
                )

                # Deduct fees and transaction costs from portfolio value
                total_costs = daily_fee + transaction_costs
                if float(total_costs) > 0:
                    cost_ratio = total_costs / portfolio_value_usd
                    for ticker in current_portfolio:
                        current_portfolio[ticker] *= 1 - cost_ratio

                progress.update(task, advance=1)

            # Convert results to DataFrame
            return pd.DataFrame(results).set_index("date")

    except Exception as e:
        logger.error(f"Error simulating portfolio: {str(e)}")
        raise


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
