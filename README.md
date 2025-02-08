# Hedge Fund Portfolio Project

A sophisticated market-neutral hedge fund portfolio strategy implementation that maintains beta neutrality through dynamic rebalancing while managing positions in both USD and CAD.

## Features

- **Market-Neutral Strategy**: Maintains balanced long and short positions
- **Beta Neutrality**: Dynamically rebalances to maintain target beta exposure
- **Multi-Currency Support**: Tracks performance in both USD and CAD
- **Automated Reporting**: Generates detailed monthly investor letters and performance reports
- **Risk Management**: Monitors and adjusts portfolio beta exposure
- **Transaction Cost Analysis**: Tracks and reports management fees and transaction costs

## Technical Architecture

- **Data Acquisition**: Uses Yahoo Finance API for market data
- **Portfolio Management**: Implements sophisticated beta calculation and rebalancing logic
- **Performance Tracking**: Calculates daily returns and portfolio metrics
- **Reporting**: Generates PDF reports and Excel exports

## Prerequisites

- Python 3.10 or higher
- Virtual environment management tool (venv recommended)
- Git for version control

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hedge_fund_portfolio.git
cd hedge_fund_portfolio
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux
python -m venv .venv
source .venv/bin/activate

# On Windows
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The project can be configured through several mechanisms:

1. **Direct Configuration** (`src/config.py`):
   - Set initial capital and exposure limits
   - Define long and short tickers
   - Adjust fee parameters
   - Modify beta tolerance thresholds

2. **YAML Configuration** (`config.yaml`):
   ```yaml
   initial_capital: 10000000
   management_fee: 0.02
   target_beta: 0.0
   rebalancing_threshold: 0.05
   tickers_long:
     - AAPL
     - MSFT
     - AMZN
     - JNJ
     - WMT
   tickers_short:
     - TSLA
     - META
     - SHOP
     - NVDA
     - BA
   ```

## Usage

1. **Basic Execution**:
```bash
python src/main.py
```

2. **Changing the Analysis Period**:
   - Open `src/config.py`
   - Modify `ANALYSIS_YEAR` and `ANALYSIS_MONTH`
   - Or use environment variables:
     ```bash
     export ANALYSIS_YEAR=2024
     export ANALYSIS_MONTH=1
     python src/main.py
     ```

3. **Customizing the Portfolio**:
   - Edit `config.yaml` to modify:
     - Ticker lists
     - Initial capital
     - Target beta
     - Management fees
     - Rebalancing thresholds

4. **Output Files**:
   - Monthly investor letter: `docs/monthly_report.pdf`
   - Performance data: `docs/portfolio_performance.xlsx`
   - Simulation logs: `hedge_fund_simulation.log`

## Testing

1. **Running Unit Tests**:
```bash
# Run all unit tests
pytest

# Run specific test file
pytest tests/unit/test_portfolio.py

# Run with coverage report
pytest --cov=src tests/
```

2. **Running Integration Tests**:
```bash
# Run integration tests
pytest -m integration

# Run all tests (unit + integration)
pytest -m "integration or not integration"
```

## Project Structure

```
hedge_fund_portfolio/
├── data/               # Market data storage
├── docs/              # Documentation and reports
├── src/               # Source code
│   ├── __init__.py
│   ├── config.py      # Configuration parameters
│   ├── data_acquisition.py
│   ├── portfolio.py   # Portfolio management
│   ├── performance.py # Performance calculations
│   ├── reporting.py   # Report generation
│   └── main.py        # Main application logic
├── tests/             # Test suite
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── requirements.txt   # Project dependencies
└── config.yaml       # User configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Yahoo Finance API for market data
- Pandas for data manipulation
- ReportLab for PDF generation 