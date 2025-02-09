"""
Reporting module for the hedge fund portfolio project.
Handles PDF report generation and Excel data export.
"""

import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict

import pandas as pd
import numpy as np
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


def generate_monthly_report(
    simulation_results: pd.DataFrame,
    market_data: pd.DataFrame,
    portfolio: Dict[str, float],
    output_dir: str = "docs",
) -> None:
    """
    Generate monthly performance report.

    Args:
        simulation_results (pd.DataFrame): Daily simulation results
        market_data (pd.DataFrame): Market data for all tickers
        portfolio (Dict[str, float]): Portfolio positions
        output_dir (str): Output directory for reports
    """
    try:
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Calculate portfolio metrics
        metrics = calculate_portfolio_metrics(simulation_results, market_data)

        # Generate report content
        report_content = [
            "# Monthly Performance Report\n",
            f"## Report Date: {datetime.now().strftime('%Y-%m-%d')}\n",
            "\n### Portfolio Summary\n",
            f"* Initial Portfolio Value (USD): ${metrics['initial_value_usd']:,.2f}",
            f"* Final Portfolio Value (USD): ${metrics['final_value_usd']:,.2f}",
            f"* Total Return: {metrics['total_return']:.2%}",
            f"* Annualized Return: {metrics['annualized_return']:.2%}",
            f"* Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
            f"* Maximum Drawdown: {metrics['max_drawdown']:.2%}",
            f"* Beta to Market: {metrics['portfolio_beta']:.2f}",
            "\n### Risk Metrics\n",
            f"* Daily Value at Risk (95%): ${metrics['var_95']:,.2f}",
            f"* Daily Value at Risk (99%): ${metrics['var_99']:,.2f}",
            f"* Daily Expected Shortfall (95%): ${metrics['es_95']:,.2f}",
            "\n### Fee Summary\n",
            f"* Total Management Fees: ${metrics['total_management_fees']:,.2f}",
            f"* Total Transaction Costs: ${metrics['total_transaction_costs']:,.2f}",
            "\n### Portfolio Composition\n",
        ]

        # Add portfolio positions
        for ticker, shares in portfolio.items():
            # Handle both DataFrame and dict market data
            if isinstance(market_data, pd.DataFrame):
                price = market_data[ticker].iloc[-1]
            else:
                price = market_data[ticker]  # For dict of numpy.float64
            value = shares * price
            report_content.append(f"* {ticker}: {shares:,.0f} shares (${value:,.2f})")

        # Write report to file
        report_path = Path(output_dir) / "monthly_report.md"
        with open(report_path, "w") as f:
            f.write("\n".join(report_content))

        logger.info(f"Monthly report generated: {report_path}")

    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        raise


def generate_performance_report(
    portfolio_data: pd.DataFrame,
    performance_metrics: dict,
    output_dir: str = "reports"
) -> str:
    """
    Generate a detailed performance report in Excel format.
    
    Args:
        portfolio_data: DataFrame with portfolio performance data
        performance_metrics: Dictionary containing performance metrics
        output_dir: Directory to save the report (default: 'reports')
    
    Returns:
        Path to the generated report file
    """
    logging.info("Generating detailed performance report...")
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Format report filename
    report_file = f"{output_dir}/portfolio_performance.xlsx"
    
    # Create Excel writer
    with pd.ExcelWriter(report_file) as writer:
        # Write portfolio data
        portfolio_data.to_excel(writer, sheet_name='Portfolio Data')
        
        # Write performance metrics
        pd.DataFrame.from_dict(
            performance_metrics,
            orient='index',
            columns=['Value']
        ).to_excel(writer, sheet_name='Performance Metrics')
    
    logging.info(f"Performance report generated: {report_file}")
    return report_file


def export_to_excel(
    daily_results: pd.DataFrame, filename: str = "docs/portfolio_performance.xlsx"
) -> None:
    """
    Export detailed performance data to Excel.

    Args:
        daily_results (pd.DataFrame): Daily portfolio performance results
        filename (str): Path to save the Excel file
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Exporting to Excel...", total=100)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Create Excel writer
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                # Daily performance sheet
                daily_results.to_excel(writer, sheet_name="Daily Performance", float_format="%.4f")
                progress.update(task, advance=30)

                # Rebalancing events sheet
                rebalancing_events = daily_results[daily_results["rebalanced"]].copy()
                rebalancing_events.to_excel(
                    writer, sheet_name="Rebalancing Events", float_format="%.4f"
                )
                progress.update(task, advance=30)

                # Calculate total return
                initial_value = daily_results["portfolio_value_usd"].iloc[0]
                final_value = daily_results["portfolio_value_usd"].iloc[-1]
                total_return = ((final_value / initial_value) - 1) * 100

                # Summary statistics sheet
                summary_stats = pd.DataFrame(
                    {
                        "Metric": [
                            "Total Return (%)",
                            "Average Daily Return (%)",
                            "Return Volatility (%)",
                            "Average Beta",
                            "Beta Volatility",
                            "Number of Rebalances",
                            "Total Management Fees",
                            "Total Transaction Costs",
                        ],
                        "Value": [
                            total_return,
                            daily_results["daily_return"].mean() * 100,
                            daily_results["daily_return"].std() * 100,
                            daily_results["portfolio_beta"].mean(),
                            daily_results["portfolio_beta"].std(),
                            daily_results["rebalanced"].sum(),
                            daily_results["management_fee"].sum(),
                            daily_results["transaction_costs"].sum(),
                        ],
                    }
                )
                summary_stats.to_excel(
                    writer, sheet_name="Summary Statistics", float_format="%.4f", index=False
                )
                progress.update(task, advance=40)

            logger.info(f"Performance data exported successfully: {filename}")

    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        raise


def calculate_portfolio_metrics(simulation_results: pd.DataFrame, market_data: pd.DataFrame) -> dict:
    """
    Calculate portfolio performance metrics from simulation results.

    Args:
        simulation_results (pd.DataFrame): Daily simulation results
        market_data (pd.DataFrame): Market data for all tickers

    Returns:
        dict: Dictionary containing calculated metrics
    """
    try:
        # Calculate basic metrics
        initial_value_usd = simulation_results["portfolio_value_usd"].iloc[0]
        final_value_usd = simulation_results["portfolio_value_usd"].iloc[-1]
        total_return = (final_value_usd / initial_value_usd) - 1
        
        # Calculate annualized return
        trading_days = len(simulation_results)
        if total_return >= 0:
            annualized_return = (1 + total_return) ** (252 / trading_days) - 1
        else:
            annualized_return = float('nan')  # Set to NaN if total_return is negative
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0.02)
        risk_free_rate = 0.02
        daily_returns = simulation_results["daily_return"]
        excess_returns = daily_returns - (risk_free_rate / 252)
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        
        # Calculate maximum drawdown
        rolling_max = simulation_results["portfolio_value_usd"].expanding().max()
        drawdowns = simulation_results["portfolio_value_usd"] / rolling_max - 1
        max_drawdown = drawdowns.min()
        
        # Calculate portfolio beta
        portfolio_beta = simulation_results["portfolio_beta"].mean()
        
        # Calculate Value at Risk
        var_95 = np.percentile(simulation_results["daily_return"], 5)
        var_99 = np.percentile(simulation_results["daily_return"], 1)
        
        # Calculate Expected Shortfall
        es_95 = simulation_results["daily_return"][simulation_results["daily_return"] <= var_95].mean()
        
        # Calculate fee metrics
        total_management_fees = simulation_results["management_fee"].sum()
        total_transaction_costs = simulation_results["transaction_costs"].sum()
        
        return {
            "initial_value_usd": initial_value_usd,
            "final_value_usd": final_value_usd,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "portfolio_beta": portfolio_beta,
            "var_95": var_95,
            "var_99": var_99,
            "es_95": es_95,
            "total_management_fees": total_management_fees,
            "total_transaction_costs": total_transaction_costs
        }
        
    except Exception as e:
        logger.error(f"Error calculating portfolio metrics: {str(e)}")
        raise
