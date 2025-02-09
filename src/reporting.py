"""
Reporting module for the hedge fund portfolio project.
Handles PDF report generation and Excel data export.
"""

import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import numpy as np
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import markdown2
from weasyprint import HTML, CSS
from pygments.formatters import HtmlFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


def markdown_to_pdf(markdown_content: str, pdf_path: str) -> None:
    """
    Convert markdown content to PDF using weasyprint with proper styling.
    
    Args:
        markdown_content (str): Content in markdown format
        pdf_path (str): Path to save the PDF file
    """
    # Convert markdown to HTML with extras for better formatting
    html_content = markdown2.markdown(
        markdown_content,
        extras=[
            "tables",
            "fenced-code-blocks",
            "header-ids",
            "break-on-newline",
            "cuddled-lists",
            "code-friendly"
        ]
    )
    
    # Get Pygments CSS for code highlighting
    code_style = HtmlFormatter().get_style_defs('.highlight')
    
    # Create CSS for better styling
    css = CSS(string=f"""
        @page {{
            margin: 1in;
            size: letter;
            @top-right {{
                content: "Page " counter(page);
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 100%;
            margin: 0 auto;
            padding: 2em;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.3em;
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 1.5em;
        }}
        h3 {{
            color: #34495e;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        code {{
            background-color: #f8f9fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: Monaco, "Courier New", monospace;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 1em;
            border-radius: 5px;
        }}
        {code_style}
    """)
    
    # Create complete HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert to PDF
    HTML(string=full_html).write_pdf(pdf_path, stylesheets=[css])
    
    logger.info(f"PDF generated with proper formatting: {pdf_path}")


def generate_monthly_report(
    simulation_results: pd.DataFrame,
    market_data: pd.DataFrame,
    portfolio: Dict[str, float],
    config: Dict[str, any],
    transaction_logs: List[Dict[str, float]],
    output_dir: str = "docs",
) -> None:
    """
    Generate monthly performance report.

    Args:
        simulation_results (pd.DataFrame): Daily simulation results
        market_data (pd.DataFrame): Market data for all tickers
        portfolio (Dict[str, float]): Portfolio positions
        config (Dict[str, any]): Configuration parameters
        transaction_logs (List[Dict[str, float]]): List of transaction logs
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
            f"## Simulation Period: {config.get('analysis_year', 2025)}-{config.get('analysis_month', 1):02d}\n",
            "\n### Market-Neutral Strategy Overview\n",
            "This portfolio follows a market-neutral strategy, which aims to generate returns regardless of market direction by maintaining equal long and short positions. Key concepts:\n",
            "* Net Exposure: The difference between long and short positions, targeted at $0 for market neutrality",
            "* Gross Exposure: The total absolute value of all positions, representing the strategy's true economic exposure",
            "* Returns: Calculated based on gross exposure to better reflect the strategy's performance\n",
            "\n### Simulation Configuration\n",
            f"* Initial Capital: ${config['initial_capital']:,.2f}",
            f"* Target Portfolio Beta: {config['target_portfolio_beta']:.1f}",
            f"* Gross Exposure: {config['gross_exposure']:.1f}x",
            f"* Management Fee Rate: {config['management_fee'] * 100:.1f}% per annum",
            f"* Transaction Fee: ${config['transaction_fee']:.2f} per share",
            "\nLong Positions:",
            "* " + ", ".join(config['tickers_long']),
            "\nShort Positions:",
            "* " + ", ".join(config['tickers_short']),
            "\n### Portfolio Summary\n",
            "Net Value (represents market neutrality):",
            f"* Initial Net Value (USD): ${metrics['initial_value_usd']:,.2f}",
            f"* Final Net Value (USD): ${metrics['final_value_usd']:,.2f}",
            "\nGross Exposure (represents true economic exposure):",
            f"* Initial Gross Exposure (USD): ${metrics['initial_gross_exposure_usd']:,.2f}",
            f"* Final Gross Exposure (USD): ${metrics['final_gross_exposure_usd']:,.2f}",
            "\nPerformance Metrics:",
            f"* Total Return (on Gross Exposure): {metrics['total_return']:.2%}" + (" (N/A - insufficient data)" if np.isnan(metrics['total_return']) else ""),
            f"* Annualized Return (on Gross Exposure): {metrics['annualized_return']:.2%}" + (" (N/A - insufficient data)" if np.isnan(metrics['annualized_return']) else ""),
            f"* Sharpe Ratio: {metrics['sharpe_ratio']:.2f}" + (" (N/A - insufficient volatility)" if np.isnan(metrics['sharpe_ratio']) else ""),
            f"* Maximum Drawdown: {metrics['max_drawdown']:.2%}",
            f"* Beta to Market: {metrics['portfolio_beta']:.2f}",
            "\n### Risk Metrics\n",
            "Note: Small or negative values in risk metrics indicate low downside risk, which is expected in a market-neutral strategy.\n",
            f"* Daily Value at Risk (95%): ${metrics['var_95']:,.4f}",
            f"* Daily Value at Risk (99%): ${metrics['var_99']:,.4f}",
            f"* Daily Expected Shortfall (95%): ${metrics['es_95']:,.4f}",
            "\n### Fee Summary\n",
            f"* Total Management Fees: ${metrics['total_management_fees']:,.2f}",
            f"* Total Transaction Costs: ${metrics['total_transaction_costs']:,.2f}",
        ]

        # Add initial portfolio composition
        report_content.append("\n### Initial Portfolio Composition\n")
        long_value = 0
        short_value = 0
        for ticker, shares in portfolio.items():
            initial_value = shares * market_data[ticker].iloc[0]
            report_content.append(f"* {ticker}: {shares:,.0f} shares (${abs(initial_value):,.2f} {'long' if shares > 0 else 'short'})")
            if shares > 0:
                long_value += initial_value
            else:
                short_value += abs(initial_value)
        report_content.extend([
            f"\nTotal Long Exposure: ${long_value:,.2f}",
            f"Total Short Exposure: ${short_value:,.2f}",
            f"Net Exposure: ${(long_value - short_value):,.2f}",
            f"Gross Exposure: ${(long_value + short_value):,.2f}"
        ])

        # Add final portfolio composition
        report_content.append("\n### Final Portfolio Composition\n")
        final_prices = market_data.iloc[-1]
        long_value = 0
        short_value = 0
        for ticker, shares in portfolio.items():
            final_value = shares * final_prices[ticker]
            report_content.append(f"* {ticker}: {shares:,.0f} shares (${abs(final_value):,.2f} {'long' if shares > 0 else 'short'})")
            if shares > 0:
                long_value += final_value
            else:
                short_value += abs(final_value)
        report_content.extend([
            f"\nTotal Long Exposure: ${long_value:,.2f}",
            f"Total Short Exposure: ${short_value:,.2f}",
            f"Net Exposure: ${(long_value - short_value):,.2f}",
            f"Gross Exposure: ${(long_value + short_value):,.2f}"
        ])

        # Add transaction logs
        report_content.append("\n### Transaction Logs\n")
        # Add table header
        report_content.extend([
            "| Date | Ticker | Shares Traded | Portfolio Beta | Transaction Cost |",
            "|------|--------|---------------|----------------|------------------|"
        ])
        # Add table rows
        for log in transaction_logs:
            date_str = log['date'].strftime('%Y-%m-%d') if hasattr(log['date'], 'strftime') else str(log['date'])
            report_content.append(
                f"| {date_str} | {log['ticker']} | {log['shares_traded']:,.2f} | {log.get('portfolio_beta', 0):,.3f} | ${log['transaction_cost']:.2f} |"
            )

        # Calculate and add totals
        total_shares = sum(abs(log['shares_traded']) for log in transaction_logs)
        total_cost = sum(log['transaction_cost'] for log in transaction_logs)
        report_content.extend([
            "|------|--------|---------------|----------------|------------------|",
            f"| **Total** | — | **{total_shares:,.2f}** | **—** | **${total_cost:.2f}** |",
            "\nNote: Transaction costs are calculated at a rate of $0.01 per share traded. Portfolio Beta shows the portfolio's beta at the time of each trade."
        ])

        # Write markdown report to file
        report_path = Path(output_dir) / "monthly_report.md"
        with open(report_path, "w") as f:
            f.write("\n".join(report_content))

        # Generate PDF version
        pdf_path = Path(output_dir) / "monthly_report.pdf"
        markdown_to_pdf("\n".join(report_content), str(pdf_path))

        logger.info(f"Monthly report generated: {report_path}")
        logger.info(f"PDF report generated: {pdf_path}")

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
        # Calculate basic metrics using gross exposure
        initial_gross_exposure = simulation_results["gross_exposure_usd"].iloc[0]
        final_gross_exposure = simulation_results["gross_exposure_usd"].iloc[-1]
        initial_value_usd = simulation_results["portfolio_value_usd"].iloc[0]
        final_value_usd = simulation_results["portfolio_value_usd"].iloc[-1]
        
        # Calculate returns based on gross exposure
        if initial_gross_exposure > 0:
            total_return = (final_gross_exposure / initial_gross_exposure) - 1
            logger.info(f"Total return based on gross exposure: {total_return:.2%}")
        else:
            logger.warning("Initial gross exposure is zero or negative")
            total_return = float('nan')
        
        # Calculate annualized return (handle edge cases)
        trading_days = len(simulation_results)
        if not np.isnan(total_return) and trading_days > 0:
            annualized_return = (1 + total_return) ** (252 / trading_days) - 1
        else:
            annualized_return = float('nan')
        
        # Calculate daily returns using gross exposure
        daily_returns = simulation_results["daily_return"]
        
        # Calculate risk-adjusted metrics
        risk_free_rate = 0.02  # 2% annual risk-free rate
        excess_returns = daily_returns - (risk_free_rate / 252)
        
        # Handle Sharpe ratio calculation with proper error handling
        returns_std = daily_returns.std()
        if returns_std > 0 and not np.isnan(returns_std):
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns_std
        else:
            sharpe_ratio = float('nan')
            logger.warning("Unable to calculate Sharpe ratio due to zero or undefined volatility")
        
        # Calculate maximum drawdown using gross exposure with error handling
        rolling_max = simulation_results["gross_exposure_usd"].expanding().max()
        drawdowns = np.where(rolling_max > 0, 
                           simulation_results["gross_exposure_usd"] / rolling_max - 1,
                           float('nan'))
        max_drawdown = float('nan') if np.all(np.isnan(drawdowns)) else np.nanmin(drawdowns)
        
        # Calculate portfolio beta
        portfolio_beta = simulation_results["portfolio_beta"].mean()
        
        # Calculate risk metrics with proper scaling and error handling
        # Convert to percentage for clearer presentation
        daily_returns_pct = daily_returns * 100
        
        # Calculate VaR with minimum sample size check
        min_samples = 15  # Minimum samples needed for reliable VaR calculation
        if len(daily_returns_pct) >= min_samples:
            var_95 = np.percentile(daily_returns_pct, 5)
            var_99 = np.percentile(daily_returns_pct, 1)
            
            # Calculate Expected Shortfall
            below_var = daily_returns_pct[daily_returns_pct <= var_95]
            es_95 = below_var.mean() if not below_var.empty else float('nan')
        else:
            var_95 = float('nan')
            var_99 = float('nan')
            es_95 = float('nan')
            logger.warning("Insufficient data for reliable VaR calculation")
        
        # Calculate fee metrics
        total_management_fees = simulation_results["management_fee"].sum()
        total_transaction_costs = simulation_results["transaction_costs"].sum()
        
        # Calculate additional market-neutral specific metrics
        avg_gross_exposure = simulation_results["gross_exposure_usd"].mean()
        avg_net_exposure = simulation_results["portfolio_value_usd"].mean()
        net_exposure_ratio = avg_net_exposure / avg_gross_exposure if avg_gross_exposure > 0 else float('nan')
        
        return {
            "initial_value_usd": initial_value_usd,
            "final_value_usd": final_value_usd,
            "initial_gross_exposure_usd": initial_gross_exposure,
            "final_gross_exposure_usd": final_gross_exposure,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "portfolio_beta": portfolio_beta,
            "var_95": var_95,
            "var_99": var_99,
            "es_95": es_95,
            "total_management_fees": total_management_fees,
            "total_transaction_costs": total_transaction_costs,
            "avg_gross_exposure": avg_gross_exposure,
            "avg_net_exposure": avg_net_exposure,
            "net_exposure_ratio": net_exposure_ratio
        }
        
    except Exception as e:
        logger.error(f"Error calculating portfolio metrics: {str(e)}")
        raise
