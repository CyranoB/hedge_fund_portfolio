"""
Main application module for the hedge fund portfolio project.
Integrates all modules to run the complete simulation.
"""

import atexit
import glob
import logging
import os
import pandas as pd
from pathlib import Path

from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config
from .data_acquisition import download_market_data, get_date_range, validate_market_data, get_exchange_rates
from .performance import calculate_daily_returns, simulate_portfolio
from .portfolio import compute_beta, initialize_portfolio, rebalance_portfolio
from .reporting import export_to_excel, generate_monthly_report


def setup_logging(log_file: str = "hedge_fund_simulation.log") -> logging.Logger:
    """Set up logging configuration.

    Args:
        log_file (str): Path to the log file. Defaults to "hedge_fund_simulation.log".

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("src.main")
    logger.setLevel(logging.INFO)

    # Create handlers
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file)

    # Create formatters and add it to handlers
    log_format = "%(asctime)s %(levelname)-8s %(message)s"
    date_format = "%y/%m/%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

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


def run_simulation(config_file: str = "config.yaml") -> pd.DataFrame:
    """Run the hedge fund portfolio simulation.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        pd.DataFrame: Simulation results.

    Raises:
        ValueError: If market data validation fails or configuration is invalid
        RuntimeError: If simulation or report generation fails
    """
    try:
        # Set up logging
        logger = setup_logging()
        logger.info("Starting hedge fund portfolio simulation...")

        # Load configuration
        config = load_config()

        # Validate required config values
        required_keys = [
            "tickers_long",
            "tickers_short",
            "market_index",
            "initial_capital",
            "gross_exposure",
            "target_portfolio_beta"
        ]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")

        # Calculate analysis period
        logger.info("Calculating analysis period...")
        start_date, end_date = get_date_range(
            config.get("analysis_year", 2024), config.get("analysis_month", 1)
        )

        # Combine all tickers
        all_tickers = config["tickers_long"] + config["tickers_short"] + [config["market_index"]]

        # Download market data
        logger.info("Downloading market data...")
        market_data = download_market_data(all_tickers, start_date, end_date)
        exchange_rates = get_exchange_rates(start_date, end_date)

        # Validate market data
        if not validate_market_data(market_data):
            logger.error("Market data validation failed")
            raise ValueError("Market data validation failed")

        # Calculate daily returns
        logger.info("Calculating daily returns...")
        returns = calculate_daily_returns(market_data)

        # Compute initial betas
        logger.info("Computing initial betas...")
        betas = {}
        for ticker in all_tickers[:-1]:  # Exclude market index
            betas[ticker] = compute_beta(returns[ticker], returns[config["market_index"]])

        # Initialize portfolio
        logger.info("Initializing portfolio...")
        initial_prices = market_data.iloc[0].to_dict()  # Convert Series to dictionary
        initial_date = market_data.index[0]  # Get the first date from market data
        portfolio, initial_transaction_cost, initial_logs = initialize_portfolio(
            config["initial_capital"],
            initial_prices,
            config["tickers_long"],
            config["tickers_short"],
            betas,
            initial_date
        )

        # Log initial portfolio value and transaction costs
        initial_portfolio_value = sum(shares * market_data.iloc[0][ticker] for ticker, shares in portfolio.items())
        logger.info(f"Initial portfolio value: ${initial_portfolio_value:,.2f}")
        logger.info(f"Initial transaction costs: ${initial_transaction_cost:.2f}")

        # Simulate portfolio performance
        logger.info("Simulating portfolio performance...")
        simulation_results, transaction_logs = simulate_portfolio(  # Capture transaction logs
            market_data,
            portfolio,
            betas,
            exchange_rates,
            config["transaction_fee"],
            config["target_portfolio_beta"]
        )

        # Add initial transaction logs to the overall logs
        transaction_logs = initial_logs + transaction_logs

        # Generate reports
        logger.info("Generating reports...")
        try:
            generate_monthly_report(simulation_results, market_data, portfolio, config, transaction_logs)  # Pass transaction logs
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            raise RuntimeError(f"Failed to generate report: {str(e)}")

        logger.info("Simulation completed successfully")
        return simulation_results

    except Exception as e:
        logger.error(f"Error during simulation: {str(e)}")
        raise


if __name__ == "__main__":
    run_simulation()
