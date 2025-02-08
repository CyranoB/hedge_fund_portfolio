"""
Main application module for the hedge fund portfolio project.
Integrates all modules to run the complete simulation.
"""

import atexit
import glob
import logging
import os
import shutil
from datetime import datetime, timedelta

from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import load_config
from src.data_acquisition import (
    download_market_data,
    get_date_range,
    get_exchange_rates,
    validate_market_data,
)
from src.performance import calculate_daily_returns, simulate_portfolio
from src.portfolio import compute_beta, initialize_portfolio, rebalance_portfolio
from src.reporting import export_to_excel, generate_monthly_report


def setup_logging(log_file="hedge_fund_simulation.log"):
    """
    Set up logging configuration with both file and console handlers.

    Args:
        log_file (str): Path to the log file

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create the logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)

    # Remove any existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    # Create and configure file handler
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="[%X]")
    )

    # Create and configure console handler
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # Configure root logger
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Get logger for this module
    logger = logging.getLogger(__name__)

    return logger


def cleanup_temp_files():
    """Clean up any temporary files created during simulation."""
    temp_patterns = ["*.tmp", "*.temp", "*_temp.*"]
    for pattern in temp_patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except Exception as e:
                logging.warning(f"Failed to remove temporary file {file}: {e}")


def run_simulation():
    """
    Run the complete hedge fund portfolio simulation.

    This function orchestrates the entire simulation workflow:
    1. Loads configuration
    2. Downloads market data
    3. Initializes portfolio
    4. Runs daily simulation
    5. Generates reports

    Returns:
        pd.DataFrame: Daily simulation results

    Raises:
        ValueError: If market data validation fails
        RuntimeError: If simulation fails
    """
    try:
        # Set up logging and cleanup
        logger = setup_logging()
        atexit.register(cleanup_temp_files)

        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()

        # Create output directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("docs", exist_ok=True)

        # Get date range for analysis
        logger.info("Calculating analysis period...")
        start_date, end_date = get_date_range(
            config.get("analysis_year", 2024), config.get("analysis_month", 1)
        )

        # Combine all tickers
        all_tickers = config["tickers_long"] + config["tickers_short"] + [config["market_index"]]

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True
        ) as progress:
            # Download market data
            progress.add_task("Downloading market data...", total=None)
            logger.info("Downloading market data...")
            market_data = download_market_data(all_tickers, start_date, end_date)

            # Validate market data
            if not validate_market_data(market_data):
                raise ValueError("Market data validation failed")

            # Get exchange rates
            progress.add_task("Retrieving exchange rates...", total=None)
            logger.info("Retrieving exchange rates...")
            exchange_rates = get_exchange_rates(start_date, end_date)

            # Calculate daily returns
            progress.add_task("Calculating returns...", total=None)
            logger.info("Calculating daily returns...")
            daily_returns = calculate_daily_returns(market_data)

            # Calculate betas for each ticker
            logger.info("Computing initial betas...")
            market_returns = daily_returns[config["market_index"]]
            betas = {}
            for ticker in all_tickers:
                if ticker != config["market_index"]:
                    betas[ticker] = compute_beta(daily_returns[ticker], market_returns)

            # Initialize portfolio
            progress.add_task("Initializing portfolio...", total=None)
            logger.info("Initializing portfolio...")
            portfolio = initialize_portfolio(
                config["initial_capital"],
                market_data,
                config["tickers_long"],
                config["tickers_short"],
            )

            # Run portfolio simulation
            progress.add_task("Simulating portfolio...", total=None)
            logger.info("Simulating portfolio performance...")
            simulation_results = simulate_portfolio(
                market_data,
                portfolio,
                daily_returns,
                exchange_rates,
                config["management_fee"],
                config["target_beta"],
            )

            # Generate reports
            progress.add_task("Generating reports...", total=None)
            logger.info("Generating reports...")

            generate_monthly_report(
                simulation_results, portfolio, betas, os.path.join("docs", "monthly_report.pdf")
            )

            export_to_excel(simulation_results, os.path.join("docs", "portfolio_performance.xlsx"))

            logger.info("Simulation completed successfully")
            return simulation_results

    except Exception as e:
        logger.error(f"Error during simulation: {str(e)}")
        raise


if __name__ == "__main__":
    run_simulation()
