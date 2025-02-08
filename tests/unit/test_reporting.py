"""
Unit tests for the reporting module.
"""

import pytest
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from src.reporting import generate_monthly_report, export_to_excel

@pytest.fixture
def sample_daily_results():
    """Fixture providing sample daily performance results."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-10", freq='B')
    np.random.seed(42)  # For reproducibility
    
    # Generate sample performance data
    data = {
        'portfolio_value_usd': 10_000_000 + np.random.normal(5000, 50000, len(dates)).cumsum(),
        'portfolio_value_cad': 13_500_000 + np.random.normal(6750, 67500, len(dates)).cumsum(),
        'portfolio_beta': np.random.normal(0, 0.1, len(dates)),
        'daily_return': np.random.normal(0.0001, 0.02, len(dates)),
        'management_fee': np.random.uniform(500, 1000, len(dates)),
        'transaction_costs': np.random.uniform(0, 2000, len(dates)),
        'rebalanced': np.random.choice([True, False], len(dates), p=[0.2, 0.8]),
        'exchange_rate': np.random.normal(1.35, 0.005, len(dates))
    }
    
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def sample_portfolio():
    """Fixture providing sample portfolio positions."""
    return {
        'AAPL': 1000,
        'MSFT': 500,
        'TSLA': -800,
        'META': -400
    }

@pytest.fixture
def sample_betas():
    """Fixture providing sample beta values."""
    return {
        'AAPL': 1.2,
        'MSFT': 1.1,
        'TSLA': 1.5,
        'META': 1.3
    }

def test_generate_monthly_report(
    sample_daily_results,
    sample_portfolio,
    sample_betas,
    tmp_path
):
    """Test PDF report generation."""
    # Set up test output path
    output_path = os.path.join(tmp_path, "test_report.pdf")
    
    # Generate report
    generate_monthly_report(
        sample_daily_results,
        sample_portfolio,
        sample_betas,
        output_path
    )
    
    # Verify file was created
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # Basic PDF validation (check if it starts with PDF header)
    with open(output_path, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF'

def test_export_to_excel(sample_daily_results, tmp_path):
    """Test Excel export functionality."""
    # Set up test output path
    output_path = os.path.join(tmp_path, "test_performance.xlsx")
    
    # Export data
    export_to_excel(sample_daily_results, output_path)
    
    # Verify file was created
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # Read back and verify contents
    with pd.ExcelFile(output_path) as excel:
        # Check sheet names
        expected_sheets = ['Daily Performance', 'Rebalancing Events', 'Summary Statistics']
        assert all(sheet in excel.sheet_names for sheet in expected_sheets)
        
        # Check daily performance data
        daily_data = pd.read_excel(excel, 'Daily Performance', index_col=0)
        assert len(daily_data) == len(sample_daily_results)
        assert all(col in daily_data.columns for col in sample_daily_results.columns)
        
        # Check rebalancing events
        rebalancing_data = pd.read_excel(excel, 'Rebalancing Events', index_col=0)
        assert len(rebalancing_data) == sample_daily_results['rebalanced'].sum()
        
        # Check summary statistics
        summary_data = pd.read_excel(excel, 'Summary Statistics')
        assert len(summary_data) == 8  # Number of metrics
        assert 'Metric' in summary_data.columns
        assert 'Value' in summary_data.columns
        
        # Verify some key metrics
        metrics = summary_data['Metric'].tolist()
        assert 'Total Return (%)' in metrics
        assert 'Average Beta' in metrics
        assert 'Number of Rebalances' in metrics 