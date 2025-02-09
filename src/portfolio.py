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


def initialize_portfolio(initial_capital: float, prices: Dict[str, float], tickers_long: List[str], tickers_short: List[str], betas: Dict[str, float], current_date) -> Tuple[Dict[str, float], float, List[Dict[str, float]]]:
    """
    Initializes the portfolio allocation based on an initial capital.
    
    Parameters:
        initial_capital (float): The total initial capital in USD.
        prices (dict): A dictionary with tickers as keys and their initial price as values.
        tickers_long (list): A list of ticker symbols to take long positions.
        tickers_short (list): A list of ticker symbols to take short positions.
        betas (dict): Dictionary of beta values per ticker.
        current_date: Current trading date.
        
    Returns:
        Tuple[Dict[str, float], float, List[Dict[str, float]]]: A tuple containing:
            - Dictionary mapping each ticker to the number of shares
            - Total transaction costs
            - List of transaction logs
    """
    portfolio = {}
    transaction_logs = []
    total_transaction_cost = 0.0
    
    # Split the initial capital equally between long and short positions.
    long_capital = initial_capital * 0.5
    short_capital = initial_capital * 0.5

    # Determine the number of positions on each side.
    num_long = len(tickers_long)
    num_short = len(tickers_short)

    # Compute allocation per ticker.
    allocation_long = long_capital / num_long
    allocation_short = short_capital / num_short

    # Calculate the number of shares for each long ticker.
    for ticker in tickers_long:
        if ticker not in prices:
            raise ValueError(f"Price for ticker {ticker} is not available.")
        # Number of shares = allocation / price, rounded to whole number
        shares = round(allocation_long / prices[ticker])
        portfolio[ticker] = shares
        
        # Calculate transaction cost and log the trade
        transaction_cost = shares * 0.01  # $0.01 per share
        total_transaction_cost += transaction_cost
        
        transaction_logs.append({
            "date": current_date,
            "ticker": ticker,
            "shares_traded": shares,
            "price": prices[ticker],
            "portfolio_beta": 0.0,  # Initial portfolio beta
            "transaction_cost": transaction_cost
        })

    # Calculate the number of shares for each short ticker.
    for ticker in tickers_short:
        if ticker not in prices:
            raise ValueError(f"Price for ticker {ticker} is not available.")
        # For short positions, the number of shares is negative, rounded to whole number
        shares = round(allocation_short / prices[ticker])
        portfolio[ticker] = -shares
        
        # Calculate transaction cost and log the trade
        transaction_cost = shares * 0.01  # $0.01 per share
        total_transaction_cost += transaction_cost
        
        transaction_logs.append({
            "date": current_date,
            "ticker": ticker,
            "shares_traded": shares,
            "price": prices[ticker],
            "portfolio_beta": 0.0,  # Initial portfolio beta
            "transaction_cost": transaction_cost
        })

    # Calculate initial portfolio beta
    positions = {ticker: shares * prices[ticker] for ticker, shares in portfolio.items()}
    initial_beta = compute_portfolio_beta(positions, betas)
    
    # Update portfolio beta in transaction logs
    for log in transaction_logs:
        log["portfolio_beta"] = initial_beta

    return portfolio, total_transaction_cost, transaction_logs


def rebalance_portfolio(
    portfolio: Dict[str, float],
    prices: pd.Series,
    betas: Dict[str, float],
    target_beta: float = 0.0,
    current_date = None,
) -> Tuple[Dict[str, float], float, List[Dict[str, float]]]:
    """
    Rebalance the portfolio to maintain market neutrality and target beta.
    All share quantities are rounded to whole numbers.
    
    Args:
        portfolio: Current portfolio positions (shares)
        prices: Current prices for all tickers
        betas: Beta values for each ticker
        target_beta: Target portfolio beta (default: 0.0 for market neutral)
        current_date: Current trading date
    
    Returns:
        Tuple[Dict[str, float], float, List[Dict[str, float]]]: Updated portfolio positions, transaction costs, and transaction logs
    """
    logging.info("Rebalancing portfolio to maintain market neutrality...")
    
    # Calculate current positions in USD
    positions = {ticker: shares * prices[ticker] for ticker, shares in portfolio.items()}
    total_value = sum(abs(val) for val in positions.values())
    
    # Calculate current portfolio beta
    current_beta = compute_portfolio_beta(positions, betas)
    
    # If beta is within tolerance, no rebalancing needed
    if abs(current_beta - target_beta) <= BETA_TOLERANCE:
        logging.info(f"Portfolio beta {current_beta:.2f} within tolerance of target {target_beta}")
        return portfolio.copy(), 0.0, []  # Return empty transaction log
    
    # Separate long and short positions
    long_positions = {t: s for t, s in portfolio.items() if s > 0}
    short_positions = {t: s for t, s in portfolio.items() if s < 0}
    
    # Calculate beta contribution of each side
    long_beta = sum(betas[t] * s * prices[t] for t, s in long_positions.items()) / total_value
    short_beta = sum(betas[t] * s * prices[t] for t, s in short_positions.items()) / total_value
    
    # Calculate required adjustments
    beta_gap = target_beta - current_beta
    if abs(long_beta) > abs(short_beta):
        long_adjustment = -beta_gap * 0.6
        short_adjustment = -beta_gap * 0.4
    else:
        long_adjustment = -beta_gap * 0.4
        short_adjustment = -beta_gap * 0.6
    
    new_portfolio = {}
    total_transaction_cost = 0.0
    transaction_logs = []  # Initialize transaction logs
    
    # Adjust long positions
    for ticker, shares in long_positions.items():
        beta_contribution = betas[ticker] * shares * prices[ticker] / total_value
        adjustment_factor = 1.0 + (long_adjustment * beta_contribution / long_beta)
        # Round to whole number of shares
        new_shares = round(shares * adjustment_factor)
        
        # Calculate transaction cost
        shares_traded = abs(new_shares - shares)
        transaction_cost = shares_traded * 0.01  # $0.01 per share
        total_transaction_cost += transaction_cost
        
        # Log transaction
        if shares_traded > 0:  # Only log if shares were actually traded
            transaction_logs.append({
                "date": current_date,
                "ticker": ticker,
                "shares_traded": shares_traded,
                "price": prices[ticker],
                "portfolio_beta": current_beta,
                "transaction_cost": transaction_cost
            })
        
        new_portfolio[ticker] = new_shares
    
    # Adjust short positions
    for ticker, shares in short_positions.items():
        beta_contribution = betas[ticker] * shares * prices[ticker] / total_value
        adjustment_factor = 1.0 + (short_adjustment * beta_contribution / short_beta)
        # Round to whole number of shares (maintaining negative sign for shorts)
        new_shares = -round(abs(shares * adjustment_factor))
        
        # Calculate transaction cost
        shares_traded = abs(new_shares - shares)
        transaction_cost = shares_traded * 0.01  # $0.01 per share
        total_transaction_cost += transaction_cost
        
        # Log transaction
        if shares_traded > 0:  # Only log if shares were actually traded
            transaction_logs.append({
                "date": current_date,
                "ticker": ticker,
                "shares_traded": shares_traded,
                "price": prices[ticker],
                "portfolio_beta": current_beta,
                "transaction_cost": transaction_cost
            })
        
        new_portfolio[ticker] = new_shares
    
    # Verify new portfolio beta
    new_positions = {ticker: shares * prices[ticker] for ticker, shares in new_portfolio.items()}
    new_beta = compute_portfolio_beta(new_positions, betas)
    logging.info(f"Portfolio rebalanced. New beta: {new_beta:.2f}")
    
    return new_portfolio, total_transaction_cost, transaction_logs
