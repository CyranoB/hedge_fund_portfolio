"""
Main application module for the hedge fund portfolio project.
Integrates all modules to run the complete simulation.
"""

import logging
import os
from datetime import datetime, timedelta
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from src.config import load_config
from src.data_acquisition import download_market_data, get_exchange_rates
from src.portfolio import initialize_portfolio, rebalance_portfolio
from src.performance import calculate_daily_returns, simulate_portfolio
from src.reporting import generate_monthly_report, export_to_excel

def setup_logging(log_file="hedge_fund_simulation.log"):
    """Set up logging configuration."""
    # Create the logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    
    # Remove any existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    
    # Create and configure file handler first
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="[%X]"
    ))
    
    # Create and configure console handler
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Configure root logger
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    
    # Log initial message
    logger.info("Starting hedge fund portfolio simulation...")
    
    return logger

def run_simulation():
    """Run the complete hedge fund portfolio simulation."""
    try:
        # Set up logging
        logger = setup_logging()
        
        # Load configuration
        config = load_config()
        
        # Set up date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Convert dates to string format
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            # Download market data
            progress.add_task("Downloading market data...", total=None)
            logger.info("Downloading market data...")
            market_data = download_market_data(config["tickers"], start_date_str, end_date_str)
            
            # Debug: Print the columns of market_data to verify structure
            print("market_data columns:", market_data.columns)
            
            # Get exchange rates
            progress.add_task("Retrieving exchange rates...", total=None)
            logger.info("Retrieving exchange rates...")
            exchange_rates = get_exchange_rates(start_date_str, end_date_str)
            
            # Calculate daily returns and betas
            progress.add_task("Calculating returns and betas...", total=None)
            logger.info("Calculating returns and betas...")
            daily_returns = calculate_daily_returns(market_data)
            
            # Initialize portfolio
            progress.add_task("Initializing portfolio...", total=None)
            logger.info("Initializing portfolio...")
            portfolio = initialize_portfolio(
                config["initial_capital"],
                market_data,
                config["tickers_long"],
                config["tickers_short"]
            )
            
            # Use the market_data directly as close prices
            # (download_market_data already extracts the close prices)
            close_prices = market_data
            
            # Run portfolio simulation
            progress.add_task("Simulating portfolio...", total=None)
            logger.info("Simulating portfolio performance...")
            simulation_results = simulate_portfolio(
                close_prices,
                portfolio,
                daily_returns,
                exchange_rates,
                config["management_fee"],
                config["target_beta"]
            )
            
            # Generate reports
            progress.add_task("Generating reports...", total=None)
            logger.info("Generating reports...")
            
            # Create docs directory if it doesn't exist
            os.makedirs("docs", exist_ok=True)
            
            generate_monthly_report(
                simulation_results,
                portfolio,
                daily_returns,
                os.path.join("docs", "monthly_report.pdf")
            )
            
            export_to_excel(
                simulation_results,
                os.path.join("docs", "portfolio_performance.xlsx")
            )
            
            logger.info("Simulation completed successfully")
            return simulation_results
            
    except Exception as e:
        logging.error(f"Error during simulation: {str(e)}")  # Use root logger for error
        raise

if __name__ == "__main__":
    run_simulation()
