# Hedge Fund Portfolio Project

This project implements a market-neutral hedge fund portfolio strategy that maintains long and short positions in selected stocks while targeting beta neutrality.

## Project Goals

- Implement a market-neutral portfolio strategy
- Maintain beta neutrality through dynamic rebalancing
- Track portfolio performance in both USD and CAD
- Generate monthly investor letters and detailed performance reports

## Setup Instructions

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

- `data/` - Market data storage
- `docs/` - Documentation and final PDF reports
- `src/` - Source code files
  - `config.py` - Configuration parameters
  - `data_acquisition.py` - Market data download
  - `portfolio.py` - Portfolio management
  - `performance.py` - Performance calculations
  - `reporting.py` - Report generation
  - `main.py` - Main application logic
- `tests/` - Unit tests

## Usage

1. Configure portfolio parameters in `src/config.py`
2. Run the simulation:
```bash
python src/main.py
```

The program will:
- Download required market data
- Initialize and manage the portfolio
- Generate performance reports
- Export results to Excel and PDF formats

## Dependencies

- pandas - Data manipulation and analysis
- numpy - Numerical computations
- yfinance - Yahoo Finance market data
- statsmodels - Statistical computations
- openpyxl - Excel file handling
- reportlab - PDF generation 