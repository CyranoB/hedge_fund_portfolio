"""
Performance module for the hedge fund portfolio project.
Handles daily returns calculation and portfolio performance simulation.
"""

import pandas as pd
import numpy as np
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from typing import Dict, Tuple, List
import logging

from src.portfolio import compute_portfolio_beta, rebalance_portfolio
from src.config import MANAGEMENT_FEE_ANNUAL, BETA_TOLERANCE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    betas: Dict[str, float],
    market_returns: pd.Series,
    exchange_rates: pd.Series,
    target_beta: float = 0
) -> pd.DataFrame:
    """
    Simulate daily portfolio performance with rebalancing and fee calculations.
    
    Args:
        daily_prices (pd.DataFrame): Daily prices for all tickers
        portfolio (Dict[str, float]): Initial portfolio positions
        betas (Dict[str, float]): Beta values for each ticker
        market_returns (pd.Series): Daily market index returns
        exchange_rates (pd.Series): Daily USD/CAD exchange rates
        target_beta (float): Target portfolio beta
    
    Returns:
        pd.DataFrame: Daily simulation results
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Simulating portfolio performance...", total=len(daily_prices))
            
            # Initialize results storage
            results = []
            current_portfolio = portfolio.copy()
            
            # Simulate each day
            for date, prices in daily_prices.iterrows():
                # Calculate current position values and portfolio metrics
                positions = {
                    ticker: shares * prices[ticker]
                    for ticker, shares in current_portfolio.items()
                }
                
                portfolio_value_usd = sum(positions.values())
                portfolio_beta = compute_portfolio_beta(positions, betas)
                
                # Check if rebalancing is needed
                rebalanced = False
                transaction_costs = 0.0
                if abs(portfolio_beta - target_beta) > BETA_TOLERANCE:
                    current_portfolio, transaction_costs = rebalance_portfolio(
                        current_portfolio,
                        prices,
                        betas,
                        target_beta=target_beta
                    )
                    rebalanced = True
                
                # Calculate daily management fee
                daily_fee = (MANAGEMENT_FEE_ANNUAL / 252) * portfolio_value_usd
                
                # Convert to CAD
                portfolio_value_cad = portfolio_value_usd * exchange_rates[date]
                
                # Calculate daily return (before fees and transaction costs)
                if len(results) > 0:
                    previous_value = results[-1]['portfolio_value_usd']
                    daily_return = (portfolio_value_usd - previous_value) / previous_value
                else:
                    daily_return = 0.0
                
                # Store daily results
                results.append({
                    'date': date,
                    'portfolio_value_usd': portfolio_value_usd,
                    'portfolio_value_cad': portfolio_value_cad,
                    'portfolio_beta': portfolio_beta,
                    'daily_return': daily_return,
                    'management_fee': daily_fee,
                    'transaction_costs': transaction_costs,
                    'rebalanced': rebalanced,
                    'exchange_rate': exchange_rates[date]
                })
                
                # Deduct fees and transaction costs from portfolio value
                total_costs = daily_fee + transaction_costs
                if total_costs > 0:
                    cost_ratio = total_costs / portfolio_value_usd
                    for ticker in current_portfolio:
                        current_portfolio[ticker] *= (1 - cost_ratio)
                
                progress.update(task, advance=1)
            
            # Convert results to DataFrame
            results_df = pd.DataFrame(results)
            results_df.set_index('date', inplace=True)
            
            logger.info("Portfolio simulation completed successfully")
            return results_df
    
    except Exception as e:
        logger.error(f"Error simulating portfolio: {str(e)}")
        raise
