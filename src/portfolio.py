"""
Portfolio module for the hedge fund portfolio project.
Handles beta calculations, portfolio initialization, and rebalancing.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from typing import Dict, Tuple, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
            positions[ticker] * betas[ticker] / total_exposure
            for ticker in positions
        )
        
        logger.debug(f"Computed portfolio beta: {weighted_beta:.4f}")
        return weighted_beta
    
    except Exception as e:
        logger.error(f"Error computing portfolio beta: {str(e)}")
        raise

def initialize_portfolio(
    initial_capital: float,
    prices: pd.DataFrame,
    tickers_long: List[str],
    tickers_short: List[str]
) -> Dict[str, float]:
    """
    Initialize the portfolio with equal allocation to long and short positions.
    
    Args:
        initial_capital (float): Initial capital in USD
        prices (pd.DataFrame): DataFrame with initial prices for all tickers
        tickers_long (List[str]): List of tickers for long positions
        tickers_short (List[str]): List of tickers for short positions
    
    Returns:
        Dict[str, float]: Dictionary mapping tickers to number of shares
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Initializing portfolio...", total=100)
            
            # Get initial prices
            initial_prices = prices.iloc[0]
            progress.update(task, advance=20)
            
            # Calculate capital per side (long/short)
            capital_per_side = initial_capital / 2
            capital_per_ticker_long = capital_per_side / len(tickers_long)
            capital_per_ticker_short = capital_per_side / len(tickers_short)
            progress.update(task, advance=20)
            
            # Initialize portfolio dictionary
            portfolio = {}
            
            # Calculate shares for long positions
            for ticker in tickers_long:
                shares = capital_per_ticker_long / initial_prices[ticker]
                portfolio[ticker] = shares
            progress.update(task, advance=30)
            
            # Calculate shares for short positions
            for ticker in tickers_short:
                shares = -capital_per_ticker_short / initial_prices[ticker]  # Negative for short
                portfolio[ticker] = shares
            progress.update(task, advance=30)
            
            logger.info("Portfolio initialized successfully")
            return portfolio
    
    except Exception as e:
        logger.error(f"Error initializing portfolio: {str(e)}")
        raise

def rebalance_portfolio(
    current_portfolio: Dict[str, float],
    day_prices: pd.Series,
    betas: Dict[str, float],
    target_beta: float = 0,
    tolerance: float = 0.05
) -> Tuple[Dict[str, float], float]:
    """
    Rebalance the portfolio to maintain beta neutrality.
    
    Args:
        current_portfolio (Dict[str, float]): Current portfolio positions
        day_prices (pd.Series): Current day's prices
        betas (Dict[str, float]): Beta values for each ticker
        target_beta (float): Target portfolio beta (default 0 for beta neutral)
        tolerance (float): Acceptable deviation from target beta
    
    Returns:
        Tuple[Dict[str, float], float]: Updated portfolio and transaction costs
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[yellow]Rebalancing portfolio...", total=100)
            
            # Calculate current positions in USD
            positions = {
                ticker: shares * day_prices[ticker]
                for ticker, shares in current_portfolio.items()
            }
            progress.update(task, advance=20)
            
            # Calculate current portfolio beta
            current_beta = compute_portfolio_beta(positions, betas)
            
            # Check if rebalancing is needed
            if abs(current_beta - target_beta) <= tolerance:
                logger.info("Portfolio within beta tolerance, no rebalancing needed")
                return current_portfolio, 0.0
            
            progress.update(task, advance=20)
            
            # Separate long and short positions
            long_positions = {t: s for t, s in current_portfolio.items() if s > 0}
            short_positions = {t: s for t, s in current_portfolio.items() if s < 0}
            
            # Calculate adjustment factor based on beta deviation
            beta_deviation = target_beta - current_beta
            # Use aggressive adjustment for faster convergence
            beta_adjustment = beta_deviation * 0.8  # Increased adjustment factor further
            progress.update(task, advance=20)
            
            # Adjust positions iteratively
            max_iterations = 30  # Increased max iterations further
            iteration = 0
            new_portfolio = current_portfolio.copy()
            total_adjustment = 0
            best_portfolio = new_portfolio.copy()
            best_beta_diff = float('inf')
            
            while iteration < max_iterations:
                # Adjust long positions
                for ticker in long_positions:
                    adjustment = beta_adjustment * abs(positions[ticker]) / betas[ticker]
                    new_shares = new_portfolio[ticker] + (adjustment / day_prices[ticker])
                    total_adjustment += abs(new_shares - new_portfolio[ticker])
                    new_portfolio[ticker] = new_shares
                
                # Adjust short positions
                for ticker in short_positions:
                    adjustment = -beta_adjustment * abs(positions[ticker]) / betas[ticker]
                    new_shares = new_portfolio[ticker] + (adjustment / day_prices[ticker])
                    total_adjustment += abs(new_shares - new_portfolio[ticker])
                    new_portfolio[ticker] = new_shares
                
                # Calculate new beta
                new_positions = {
                    ticker: shares * day_prices[ticker]
                    for ticker, shares in new_portfolio.items()
                }
                new_beta = compute_portfolio_beta(new_positions, betas)
                
                # Track best portfolio
                current_beta_diff = abs(new_beta - target_beta)
                if current_beta_diff < best_beta_diff:
                    best_beta_diff = current_beta_diff
                    best_portfolio = new_portfolio.copy()
                
                # Check if target reached
                if current_beta_diff <= tolerance:
                    break
                
                # Update adjustment factor with adaptive damping
                beta_deviation = target_beta - new_beta
                damping_factor = max(0.2, 1.0 - iteration/max_iterations)  # Less aggressive damping
                beta_adjustment = beta_deviation * 0.8 * damping_factor  # More aggressive base adjustment
                
                # If we're getting worse, try reversing direction
                if iteration > 0 and current_beta_diff > best_beta_diff * 1.5:
                    beta_adjustment = -beta_adjustment * 0.5
                
                iteration += 1
            
            # Use the best portfolio we found if we didn't converge
            if abs(new_beta - target_beta) > tolerance:
                new_portfolio = best_portfolio
                new_positions = {
                    ticker: shares * day_prices[ticker]
                    for ticker, shares in new_portfolio.items()
                }
                new_beta = compute_portfolio_beta(new_positions, betas)
            
            progress.update(task, advance=40)
            
            # Calculate transaction costs
            from src.config import TRANSACTION_FEE_PER_SHARE
            transaction_costs = total_adjustment * TRANSACTION_FEE_PER_SHARE
            
            logger.info(f"Portfolio rebalanced. Transaction costs: ${transaction_costs:.2f}")
            return new_portfolio, transaction_costs
    
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {str(e)}")
        raise
