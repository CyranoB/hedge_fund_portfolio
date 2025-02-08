# Hedge Fund Portfolio Project - Story Points

1. **Project Setup and Repository Structure**  
   - [x] **Create the Project Folder Structure**  
     - [x] Inside the root, create the following subdirectories:
       - [x] `data/` – for storing market data files.
       - [x] `docs/` – for documentation and the final PDF report.
       - [x] `src/` – for all source code files.
       - [x] `tests/` – for unit tests and other testing resources.
   - [x] **Create Core Files and Artifacts**  
     - [x] In the `src/` folder, create:
       - [x] `__init__.py` (to make the folder a Python package).
       - [x] `config.py`
       - [x] `data_acquisition.py`
       - [x] `portfolio.py`
       - [x] `performance.py`
       - [x] `reporting.py`
       - [x] `main.py`
     - [x] Create `requirements.txt` in the root with the following dependencies:
       - [x] `pandas`
       - [x] `numpy`
       - [x] `yfinance`
       - [x] `statsmodels`
       - [x] `openpyxl`
       - [x] `reportlab` (or any alternative for PDF generation)
     - [x] Create a `README.md` file outlining project goals, setup instructions, and usage.

2. **Implement Configuration Module (`config.py`)**  
   - [ ] **Define Portfolio Parameters and Global Variables**  
     - [ ] Set the initial capital:
       - [ ] `INITIAL_CAPITAL_USD = 10_000_000`
     - [ ] Define portfolio exposure:
       - [ ] `GROSS_EXPOSURE = 10_000_000`
   - [ ] **Define Ticker Lists**  
     - [ ] For long positions, add the following tickers:
       - [ ] `LONG_TICKERS = ['AAPL', 'MSFT', 'AMZN', 'JNJ', 'WMT']`
     - [ ] For short positions, add the following tickers:
       - [ ] `SHORT_TICKERS = ['TSLA', 'META', 'SHOP', 'NVDA', 'BA']`
     - [ ] Specify the market index ticker:
       - [ ] `MARKET_INDEX = '^GSPC'`
   - [ ] **Define Fee Parameters**  
     - [ ] Set annual management fee:
       - [ ] `MANAGEMENT_FEE_ANNUAL = 0.02`  (i.e., 2% per year)
     - [ ] Set transaction fee per share:
       - [ ] `TRANSACTION_FEE_PER_SHARE = 0.01`
   - [ ] **Set the Analysis Period and Rebalancing Tolerance**  
     - [ ] Define the month and year for simulation:
       - [ ] `ANALYSIS_YEAR = 2025`
       - [ ] `ANALYSIS_MONTH = 1`  (January)
     - [ ] Set the beta tolerance threshold:
       - [ ] `BETA_TOLERANCE = 0.05`

3. **Implement Data Acquisition Module (`data_acquisition.py`)**  
   - [ ] **Import Required Libraries**  
     - [ ] Import `yfinance` for data download.
     - [ ] Import `pandas` for data manipulation.
   - [ ] **Implement Date Range Calculation**  
     - [ ] Create a function `get_date_range(year, month)` that:
       - [ ] Accepts `year` and `month` as input.
       - [ ] Calculates and returns the start and end dates for the given month (e.g., using `pandas.Period` or similar).
   - [ ] **Download Market Data**  
     - [ ] Create a function `download_market_data(tickers, start_date, end_date)` that:
       - [ ] Uses `yfinance.download` to retrieve historical adjusted close prices for all given tickers.
       - [ ] Returns a `DataFrame` with the prices indexed by date.
       - [ ] Handles missing data (filtering out non-trading days).
   - [ ] **Implement Exchange Rate Data Retrieval**  
     - [ ] Either:
       - [ ] Download USD/CAD exchange rate data via an API or CSV.
       - [ ] OR simulate a constant rate for testing purposes.
     - [ ] Ensure exchange rates are stored in a time-indexed structure (e.g., a `Series`).
   - [ ] **Data Validation and Cleaning**  
     - [ ] Ensure all tickers have data for the entire period.
     - [ ] Align all datasets by date.

4. **Implement Portfolio Module (`portfolio.py`)**  
   - [ ] **Import Required Libraries**  
     - [ ] Import `numpy`, `pandas`, and `statsmodels.api` for regression analysis.
   - [ ] **Implement Beta Calculation for Individual Stocks**  
     - [ ] Create function `compute_beta(stock_returns, market_returns)` that:
       - [ ] Accepts two `Series`: one for stock returns and one for market returns.
       - [ ] Uses OLS regression (via `statsmodels`) to compute beta.
       - [ ] Returns the beta coefficient.
   - [ ] **Implement Portfolio Beta Calculation**  
     - [ ] Create function `compute_portfolio_beta(positions, betas)` that:
       - [ ] Accepts a dictionary of positions (ticker: position value) and a dictionary of individual betas.
       - [ ] Computes a weighted average beta (using absolute position exposures for normalization).
       - [ ] Returns the aggregated portfolio beta.
   - [ ] **Initialize the Portfolio**  
     - [ ] Create function `initialize_portfolio(initial_capital, prices, tickers_long, tickers_short)` that:
       - [ ] Splits the capital equally for long and short positions.
       - [ ] Calculates dollar allocation per ticker for each group.
       - [ ] Divides the allocated capital by the initial price of each ticker to get the number of shares.
       - [ ] For short positions, assign a negative number of shares.
       - [ ] Returns a dictionary mapping each ticker to its number of shares.
   - [ ] **Implement Portfolio Rebalancing Logic**  
     - [ ] Create function `rebalance_portfolio(current_portfolio, day_prices, betas)` that:
       - [ ] Checks if the portfolio beta deviates beyond `BETA_TOLERANCE`.
       - [ ] Recalculates the desired weights to achieve beta neutrality.
       - [ ] Adjusts the number of shares for each ticker accordingly.
       - [ ] Calculates and logs transaction fees based on `TRANSACTION_FEE_PER_SHARE`.
       - [ ] Returns the updated portfolio along with any transaction cost details.

5. **Implement Performance Module (`performance.py`)**  
   - [ ] **Import Required Libraries**  
     - [ ] Import `pandas` and any additional libraries for calculations.
   - [ ] **Calculate Daily Returns**  
     - [ ] Implement logic to compute daily returns from the adjusted close prices:
       - [ ] Ensure that returns are computed for every ticker.
       - [ ] Handle any missing data points appropriately.
   - [ ] **Simulate Daily Portfolio Performance**  
     - [ ] Create function `simulate_portfolio(daily_prices, portfolio, betas, market_returns, exchange_rates)` that:
       - [ ] Iterates over each trading day in the simulation period.
       - [ ] For each day:
         - [ ] Extract current prices from the `daily_prices` DataFrame.
         - [ ] Calculate the current position value for each ticker (number of shares × current price).
         - [ ] Sum the absolute position values to compute total portfolio exposure.
         - [ ] Calculate the daily return of the portfolio.
         - [ ] Compute the portfolio beta using `compute_portfolio_beta`.
         - [ ] Check if the portfolio beta exceeds `BETA_TOLERANCE`:
           - [ ] If yes, trigger rebalancing by calling `rebalance_portfolio` and record the event.
         - [ ] Apply daily management fees:
           - [ ] Calculate fee as `(MANAGEMENT_FEE_ANNUAL / 252) * portfolio_value`.
           - [ ] Deduct the fee from the portfolio value.
         - [ ] Convert the portfolio value from USD to CAD using the day's exchange rate.
         - [ ] Log all details for the day (date, portfolio values in USD and CAD, daily return, beta, rebalancing flag).
       - [ ] Return a DataFrame with daily simulation results.

6. **Implement Reporting Module (`reporting.py`)**  
   - [ ] **Import Required Libraries**  
     - [ ] Import `pandas` for data export.
     - [ ] Import `reportlab` (or an alternative) for PDF generation.
     - [ ] (Optionally) Import `jinja2` if using templated reports.
   - [ ] **Generate the Monthly Investor Letter (PDF Report)**  
     - [ ] Create a function `generate_monthly_report(daily_results, portfolio, beta_dict)` that:
       - [ ] Compiles a summary including:
         - [ ] Introduction to the strategy.
         - [ ] Justification of the selected long and short tickers.
         - [ ] Summary of monthly performance in both USD and CAD.
         - [ ] Evolution of portfolio beta (initial, daily changes, final beta).
         - [ ] Details and rationale for any rebalancing events.
         - [ ] Conclusion and outlook.
       - [ ] Formats the report (using plain text, HTML, or a template).
       - [ ] Converts the formatted report into a PDF file.
   - [ ] **Export Detailed Performance Data to Excel**  
     - [ ] Create a function `export_to_excel(daily_df, filename='portfolio_performance.xlsx')` that:
       - [ ] Uses `pandas.ExcelWriter` to write:
         - [ ] Daily performance data (date, USD/CAD values, beta, etc.) on one sheet.
         - [ ] Additional sheets for rebalancing logs and beta calculations, if desired.
       - [ ] Saves the Excel file with the given filename.

7. **Implement Main Application Logic (`main.py`)**  
   - [ ] **Integrate All Modules**  
     - [ ] Import configuration from `config.py`.
     - [ ] Import functions from `data_acquisition.py`, `portfolio.py`, `performance.py`, and `reporting.py`.
   - [ ] **Main Execution Workflow**  
     - [ ] Retrieve the analysis period by calling `get_date_range(ANALYSIS_YEAR, ANALYSIS_MONTH)`.
     - [ ] Download market data for:
       - [ ] All tickers in `LONG_TICKERS`, `SHORT_TICKERS`, and the `MARKET_INDEX`.
     - [ ] Retrieve or simulate USD/CAD exchange rates.
     - [ ] Initialize the portfolio:
       - [ ] Use the first available day's prices to compute the number of shares for each ticker via `initialize_portfolio`.
     - [ ] Compute initial betas for each ticker:
       - [ ] Calculate returns for each ticker and the market index.
       - [ ] Use `compute_beta` to estimate betas.
     - [ ] Run the daily simulation by calling `simulate_portfolio` with all required parameters.
     - [ ] Generate the monthly report:
       - [ ] Call `generate_monthly_report` with the simulation results.
     - [ ] Export detailed performance data to an Excel file:
       - [ ] Call `export_to_excel`.
   - [ ] **Error Handling and Logging**  
     - [ ] Integrate Python's `logging` module to record events, errors, and rebalancing triggers.
     - [ ] Use try/except blocks where necessary (e.g., during data downloads or calculations).

8. **Documentation, Testing, and Quality Assurance**  
   - [ ] **Documentation**  
     - [ ] Add comprehensive docstrings to every function and module.
     - [ ] Comment key parts of the code to explain the logic behind beta calculations, rebalancing, fees, etc.
     - [ ] Update `README.md` with:
       - [ ] Project overview.
       - [ ] Installation instructions.
       - [ ] Usage guidelines.
       - [ ] Instructions on how to change the analysis period and other parameters.
   - [ ] **Unit Testing**  
     - [ ] Create unit tests in the `tests/` directory for:
       - [ ] The `compute_beta` function (with sample data).
       - [ ] Portfolio initialization (checking correct share allocation).
       - [ ] The simulation function (ensuring expected DataFrame structure and values).
       - [ ] Rebalancing logic (ensuring beta neutrality is restored when triggered).
   - [ ] **Code Quality**  
     - [ ] Ensure adherence to PEP 8 style guidelines.
     - [ ] Run static analysis tools (like `flake8` or `pylint`) to verify code quality.

9. **Final Integration and Validation**  
   - [ ] **Run the Full Simulation**  
     - [ ] Execute the complete program for the analysis period (February 2025).
     - [ ] Validate that the simulation runs without errors.
   - [ ] **Verify Outputs**  
     - [ ] Confirm that the daily simulation DataFrame contains correct values (USD/CAD portfolio values, beta, flags).
     - [ ] Check that the PDF report (monthly investor letter) is generated and includes:
       - [ ] Strategy justification.
       - [ ] Performance summary.
       - [ ] Beta evolution and rebalancing details.
     - [ ] Verify that the Excel file is created with multiple sheets (daily performance, rebalancing logs, beta calculations).
   - [ ] **Review Logging and Error Handling**  
     - [ ] Inspect log files (or console output) for any errors or warnings during the simulation.

10. **Submission and Delivery**  
    - [ ] **Prepare the Final Deliverables**  
      - [ ] Ensure the PDF report is finalized and formatted correctly.
      - [ ] Confirm that the Excel file with detailed performance analysis is accurate and complete.
    - [ ] **Email Submission**  
      - [ ] By January 31, 2025, send an email to `Jonathan.plante@hec.ca` with:
        - [ ] The names of the teams and all participants.
        - [ ] The long and short tickers that comprise the portfolio.
      - [ ] Before March 14, 2025, email:
        - [ ] The final PDF report (monthly investor letter).
        - [ ] The Excel file with all analysis details.
    - [ ] **Final Checks**  
      - [ ] Verify that no submission deadlines are missed.
      - [ ] Double-check that all requirements (e.g., fee calculations, exchange rate conversion, beta reporting) are documented in the report.

---

Following this detailed checklist will help an AI coding agent—or any developer—implement the full solution step by step. Each story point is broken down into actionable, testable tasks ensuring that all necessary data and functionality are incorporated into the final deliverable.