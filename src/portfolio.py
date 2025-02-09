"""
Portfolio module for the hedge fund portfolio project.
Handles beta calculations, portfolio initialization, and rebalancing.
"""

import logging
from typing import Dict, List, Tuple

import pandas as pd
import statsmodels.api as sm
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from .config import BETA_TOLERANCE, MARKET_INDEX

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


def compute_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate beta coefficient using OLS regression.

    Args:
        stock_returns (pd.Series): Daily returns for a stock
        market_returns (pd.Series): Daily returns for the market index

    Returns:
        float: Beta coefficient
    """
    try:
        # Add constant to market returns for regression
        X = sm.add_constant(market_returns)

        # Perform regression
        model = sm.OLS(stock_returns, X)
        results = model.fit()

        # Extract beta (slope coefficient)
        beta = float(results.params.iloc[1])  # Changed to use iloc instead of index

        logger.debug(f"Computed beta: {beta:.4f}")
        return beta

    except Exception as e:
        logger.error(f"Error computing beta: {str(e)}")
        raise


def compute_portfolio_beta(positions: Dict[str, float], betas: Dict[str, float]) -> float:
    """
    Calculate the weighted average beta for the entire portfolio.

    Args:
        positions (Dict[str, float]): Dictionary mapping tickers to position values
        betas (Dict[str, float]): Dictionary mapping tickers to their beta values

    Returns:
        float: Portfolio beta
    """
    try:
        total_exposure = sum(abs(value) for value in positions.values())

        if total_exposure == 0:
            raise ValueError("Total portfolio exposure cannot be zero")

        # Calculate weighted average beta
        weighted_beta = sum(
            positions[ticker] * betas.get(ticker, 0) / total_exposure
            for ticker in positions
            if ticker in betas  # Only include tickers that have beta values
        )

        logger.debug(f"Computed portfolio beta: {weighted_beta:.4f}")
        return weighted_beta

    except Exception as e:
        logger.error(f"Error computing portfolio beta: {str(e)}")
        raise


def initialize_portfolio(
    initial_capital: float,
    tickers_long: List[str],
    tickers_short: List[str],
    betas: Dict[str, float],
    target_portfolio_beta: float,
    gross_exposure: float,
    initial_prices: pd.Series
) -> Dict[str, float]:
    """
    Initialize a portfolio with positions for long and short tickers that achieve the
    desired gross exposure and target portfolio beta.

    For target beta = 0, compute the total dollar allocation for longs and shorts such that:
      L = initial_capital * gross_exposure * (avg_short_beta) / (avg_long_beta + avg_short_beta)
      S = initial_capital * gross_exposure - L
    Then, allocate these exposures equally among the tickers on each side.

    Args:
        initial_capital (float): The starting capital.
        tickers_long (list of str): Tickers for long positions.
        tickers_short (list of str): Tickers for short positions.
        betas (dict): Dictionary mapping each ticker to its beta.
        target_portfolio_beta (float): The target beta for the portfolio (typically 0).
        gross_exposure (float): Desired gross exposure (e.g., 1.5).
        initial_prices (pd.Series): Initial prices for each ticker.

    Returns:
        dict: A dictionary mapping tickers to their number of shares (positive for longs,
              negative for shorts).
    """
    total_exposure = initial_capital * gross_exposure

    # Compute average beta for each side.
    avg_long_beta = sum(betas[ticker] for ticker in tickers_long) / len(tickers_long)
    avg_short_beta = sum(betas[ticker] for ticker in tickers_short) / len(tickers_short)

    # For a market-neutral (beta = 0) portfolio, the long and short exposures must offset each other.
    # Calculate the total long exposure (L) and short exposure (S).
    L = total_exposure * (avg_short_beta) / (avg_long_beta + avg_short_beta)
    S = total_exposure - L

    portfolio = {}

    # Allocate long exposure equally among long tickers based on initial prices.
    for ticker in tickers_long:
        portfolio[ticker] = (L / len(tickers_long)) / initial_prices[ticker]

    # Allocate short exposure equally among short tickers (using negative allocations) based on initial prices.
    for ticker in tickers_short:
        portfolio[ticker] = - (S / len(tickers_short)) / initial_prices[ticker]

    return portfolio


def rebalance_portfolio(
    portfolio: Dict[str, float],
    prices: pd.Series,
    betas: Dict[str, float],
    target_beta: float = 0.0,
) -> Tuple[Dict[str, float], float]:
    """
    Rebalance the portfolio to maintain market neutrality and target beta.
    
    Args:
        portfolio: Current portfolio positions (shares)
        prices: Current prices for all tickers
        betas: Beta values for each ticker
        target_beta: Target portfolio beta (default: 0.0 for market neutral)
    
    Returns:
        Tuple[Dict[str, float], float]: Updated portfolio positions and transaction costs
    """
    logging.info("Rebalancing portfolio to maintain market neutrality...")
    
    # Calculate current positions in USD
    positions = {ticker: shares * prices[ticker] for ticker, shares in portfolio.items()}
    
    # Calculate current portfolio beta
    current_beta = compute_portfolio_beta(positions, betas)
    
    # If beta is within tolerance, no rebalancing needed
    if abs(current_beta - target_beta) <= BETA_TOLERANCE:
        logging.info(f"Portfolio beta {current_beta:.2f} within tolerance of target {target_beta}")
        return portfolio.copy(), 0.0
    
    # Calculate total long and short exposure
    long_exposure = sum(value for value in positions.values() if value > 0)
    short_exposure = abs(sum(value for value in positions.values() if value < 0))
    
    # Calculate adjustment factor to achieve target beta
    beta_adjustment = (target_beta - current_beta) / 2
    
    # Adjust positions to achieve target beta
    new_portfolio = {}
    total_transaction_cost = 0.0
    
    for ticker, shares in portfolio.items():
        # Calculate adjustment based on beta difference
        adjustment = beta_adjustment * abs(shares) * betas[ticker]
        
        # Convert adjustment to shares
        new_shares = shares + (adjustment / prices[ticker])
        
        # Calculate transaction cost
        shares_traded = abs(new_shares - shares)
        transaction_cost = shares_traded * 0.01  # $0.01 per share
        total_transaction_cost += transaction_cost
        
        new_portfolio[ticker] = new_shares
    
    # Verify new portfolio beta
    new_positions = {ticker: shares * prices[ticker] for ticker, shares in new_portfolio.items()}
    new_beta = compute_portfolio_beta(new_positions, betas)
    logging.info(f"Portfolio rebalanced. New beta: {new_beta:.2f}")
    
    return new_portfolio, total_transaction_cost
