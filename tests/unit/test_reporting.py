"""
Unit tests for the reporting module.
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path

from src.reporting import generate_monthly_report


def test_generate_monthly_report(tmp_path):
    """Test monthly report generation."""
    # Create sample data
    dates = pd.date_range(start="2025-01-01", end="2025-01-10", freq="B")
    simulation_results = pd.DataFrame(
        {
            "portfolio_value_usd": np.random.uniform(9500000, 10500000, len(dates)),
            "portfolio_value_cad": np.random.uniform(12000000, 13000000, len(dates)),
            "portfolio_beta": np.random.normal(0, 0.1, len(dates)),
            "daily_return": np.random.normal(0.001, 0.02, len(dates)),
            "management_fee": np.random.uniform(500, 1000, len(dates)),
            "transaction_costs": np.random.uniform(0, 2000, len(dates)),
            "rebalanced": np.random.choice([True, False], len(dates), p=[0.2, 0.8]),
            "exchange_rate": np.random.normal(1.35, 0.005, len(dates))
        },
        index=dates
    )

    # Create sample market data
    market_data = pd.DataFrame(
        {
            "AAPL": np.random.uniform(180, 190, len(dates)),
            "MSFT": np.random.uniform(380, 400, len(dates)),
            "TSLA": np.random.uniform(220, 240, len(dates)),
            "META": np.random.uniform(360, 380, len(dates))
        },
        index=dates
    )

    # Create sample portfolio
    portfolio = {
        "AAPL": 1000,
        "MSFT": 500,
        "TSLA": -800,
        "META": -400
    }

    # Change to temporary directory
    os.chdir(tmp_path)

    # Generate report
    generate_monthly_report(simulation_results, market_data, portfolio)

    # Verify report was created
    report_path = Path("docs/monthly_report.md")
    assert report_path.exists()

    # Check report contents
    with open(report_path) as f:
        content = f.read()
        assert "Monthly Performance Report" in content
        assert "Portfolio Summary" in content
        assert "Risk Metrics" in content
        assert "Fee Summary" in content
        assert "Portfolio Composition" in content
