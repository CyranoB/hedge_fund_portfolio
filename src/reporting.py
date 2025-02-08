"""
Reporting module for the hedge fund portfolio project.
Handles PDF report generation and Excel data export.
"""

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from typing import Dict, List, Union
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

def generate_monthly_report(
    daily_results: pd.DataFrame,
    portfolio: Dict[str, float],
    beta_dict: Union[pd.DataFrame, Dict[str, float]],
    output_path: str = "docs/monthly_report.pdf"
) -> None:
    """
    Generate monthly investor letter in PDF format.
    
    Args:
        daily_results (pd.DataFrame): Daily portfolio performance results
        portfolio (Dict[str, float]): Final portfolio positions
        beta_dict (Union[pd.DataFrame, Dict[str, float]]): Beta values for each ticker
        output_path (str): Path to save the PDF report
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Generating monthly report...", total=100)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph("Monthly Investor Letter", title_style))
            progress.update(task, advance=10)
            
            # Add strategy introduction
            story.append(Paragraph("Strategy Overview", styles['Heading2']))
            story.append(Paragraph(
                """Our market-neutral hedge fund strategy aims to generate consistent returns 
                while maintaining minimal exposure to overall market movements. We achieve this 
                through a balanced portfolio of long and short positions in carefully selected 
                stocks.""",
                styles['Normal']
            ))
            story.append(Spacer(1, 12))
            progress.update(task, advance=10)
            
            # Portfolio composition
            story.append(Paragraph("Portfolio Composition", styles['Heading2']))
            long_positions = {k: v for k, v in portfolio.items() if v > 0}
            short_positions = {k: v for k, v in portfolio.items() if v < 0}
            
            # Get the beta values
            if isinstance(beta_dict, pd.DataFrame):
                latest_betas = beta_dict.iloc[-1]
            else:
                latest_betas = beta_dict
            
            # Create tables for long and short positions
            position_data = [["Position Type", "Ticker", "Shares", "Beta"]]
            for ticker, shares in long_positions.items():
                position_data.append(["Long", ticker, f"{shares:.0f}", f"{latest_betas[ticker]:.2f}"])
            for ticker, shares in short_positions.items():
                position_data.append(["Short", ticker, f"{shares:.0f}", f"{latest_betas[ticker]:.2f}"])
            
            position_table = Table(position_data)
            position_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(position_table)
            story.append(Spacer(1, 12))
            progress.update(task, advance=20)
            
            # Performance summary
            story.append(Paragraph("Performance Summary", styles['Heading2']))
            
            # Calculate key metrics
            initial_value_usd = daily_results['portfolio_value_usd'].iloc[0]
            final_value_usd = daily_results['portfolio_value_usd'].iloc[-1]
            total_return = (final_value_usd - initial_value_usd) / initial_value_usd * 100
            
            total_fees = daily_results['management_fee'].sum()
            total_costs = daily_results['transaction_costs'].sum()
            num_rebalances = daily_results['rebalanced'].sum()
            
            avg_beta = daily_results['portfolio_beta'].mean()
            max_beta = daily_results['portfolio_beta'].max()
            min_beta = daily_results['portfolio_beta'].min()
            
            metrics_data = [
                ["Metric", "Value"],
                ["Total Return", f"{total_return:.2f}%"],
                ["Initial Value (USD)", f"${initial_value_usd:,.2f}"],
                ["Final Value (USD)", f"${final_value_usd:,.2f}"],
                ["Management Fees", f"${total_fees:,.2f}"],
                ["Transaction Costs", f"${total_costs:,.2f}"],
                ["Number of Rebalances", f"{num_rebalances:d}"],
                ["Average Beta", f"{avg_beta:.3f}"],
                ["Beta Range", f"{min_beta:.3f} to {max_beta:.3f}"]
            ]
            
            metrics_table = Table(metrics_data)
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metrics_table)
            progress.update(task, advance=30)
            
            # Rebalancing analysis
            story.append(Spacer(1, 12))
            story.append(Paragraph("Portfolio Rebalancing Analysis", styles['Heading2']))
            rebalance_dates = daily_results[daily_results['rebalanced']].index
            if len(rebalance_dates) > 0:
                rebalancing_text = f"""The portfolio required rebalancing on {len(rebalance_dates)} 
                occasions to maintain the target beta exposure. Major rebalancing events occurred on: 
                {', '.join(d.strftime('%Y-%m-%d') for d in rebalance_dates[:3])}..."""
            else:
                rebalancing_text = "The portfolio maintained its target beta exposure without requiring rebalancing."
            story.append(Paragraph(rebalancing_text, styles['Normal']))
            progress.update(task, advance=20)
            
            # Build and save the PDF
            doc.build(story)
            progress.update(task, advance=10)
            
            logger.info(f"Monthly report generated successfully: {output_path}")
    
    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        raise

def export_to_excel(
    daily_results: pd.DataFrame,
    filename: str = "docs/portfolio_performance.xlsx"
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
            console=console
        ) as progress:
            task = progress.add_task("[green]Exporting to Excel...", total=100)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Create Excel writer
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Daily performance sheet
                daily_results.to_excel(
                    writer,
                    sheet_name='Daily Performance',
                    float_format='%.4f'
                )
                progress.update(task, advance=30)
                
                # Rebalancing events sheet
                rebalancing_events = daily_results[daily_results['rebalanced']].copy()
                rebalancing_events.to_excel(
                    writer,
                    sheet_name='Rebalancing Events',
                    float_format='%.4f'
                )
                progress.update(task, advance=30)
                
                # Summary statistics sheet
                summary_stats = pd.DataFrame({
                    'Metric': [
                        'Total Return (%)',
                        'Average Daily Return (%)',
                        'Return Volatility (%)',
                        'Average Beta',
                        'Beta Volatility',
                        'Number of Rebalances',
                        'Total Management Fees',
                        'Total Transaction Costs'
                    ],
                    'Value': [
                        ((daily_results['portfolio_value_usd'].iloc[-1] /
                          daily_results['portfolio_value_usd'].iloc[0] - 1) * 100),
                        daily_results['daily_return'].mean() * 100,
                        daily_results['daily_return'].std() * 100,
                        daily_results['portfolio_beta'].mean(),
                        daily_results['portfolio_beta'].std(),
                        daily_results['rebalanced'].sum(),
                        daily_results['management_fee'].sum(),
                        daily_results['transaction_costs'].sum()
                    ]
                })
                summary_stats.to_excel(
                    writer,
                    sheet_name='Summary Statistics',
                    float_format='%.4f',
                    index=False
                )
                progress.update(task, advance=40)
            
            logger.info(f"Performance data exported successfully: {filename}")
    
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        raise
