"""
Configuration module for the hedge fund portfolio project.
Contains all global parameters and settings used throughout the application.
"""

import os
from typing import Any, Dict

import yaml

# Portfolio Parameters
INITIAL_CAPITAL_USD = 10_000_000
GROSS_EXPOSURE = 10_000_000

# Ticker Lists
LONG_TICKERS = ["AAPL", "MSFT", "AMZN", "JNJ", "WMT"]
SHORT_TICKERS = ["TSLA", "META", "SHOP", "NVDA", "BA"]
MARKET_INDEX = "^GSPC"

# Fee Parameters
MANAGEMENT_FEE_ANNUAL = 0.02  # 2% per year
TRANSACTION_FEE_PER_SHARE = 0.01

# Analysis Period and Rebalancing Settings
ANALYSIS_YEAR = 2025
ANALYSIS_MONTH = 1  # January
BETA_TOLERANCE = 0.05


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

    # Default configuration
    default_config = {
        "tickers_long": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
        "tickers_short": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "market_index": "^GSPC",
        "initial_capital": 1000000,  # $1M USD
        "management_fee": 0.02,  # 2% annual management fee
        "target_beta": 0.8,  # Target portfolio beta
        "rebalancing_threshold": 0.1,  # 10% threshold for rebalancing
        "transaction_fee": 0.001,  # 0.1% transaction cost
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                # Merge with defaults, keeping user values where specified
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
        else:
            config = default_config
            # Save default config
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)

        # Add combined tickers for convenience
        config["tickers"] = (
            config["tickers_long"] + config["tickers_short"] + [config["market_index"]]
        )

        return config

    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return default_config
