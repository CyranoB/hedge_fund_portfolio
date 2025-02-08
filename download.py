import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def download_stock_data(symbols, start_date, end_date):
    """
    Download historical data for multiple stock symbols
    Returns a dictionary with symbol as key and historical data as value
    """
    stock_data = {}
    for symbol in symbols:
        # Create a Ticker object
        ticker = yf.Ticker(symbol)
        
        # Download historical data
        hist_data = ticker.history(start=start_date, end=end_date)
        stock_data[symbol] = hist_data
        
        print(f"Downloaded data for {symbol}")
    
    return stock_data

def save_stock_data(data, output_file='stock_data.xlsx'):
    """
    Save stock data to Excel with one tab per ticker
    Each tab will be named after the stock symbol
    """
    # Create Excel writer object
    with pd.ExcelWriter(output_file, engine='openpyxl', 
                       datetime_format='YYYY-MM-DD',  # This is just the default
                       mode='w') as writer:
        for symbol, df in data.items():
            # Convert timezone-aware timestamps to timezone-naive
            df_copy = df.copy()
            df_copy.index = df_copy.index.tz_localize(None)
            
            # Reset index to make the date a column
            df_copy = df_copy.reset_index()
            
            # Rename the index column to 'Date'
            df_copy = df_copy.rename(columns={'index': 'Date'})
            
            # Ensure numeric columns are float
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                df_copy[col] = df_copy[col].astype(float)
            
            # Save each dataframe to a separate worksheet
            df_copy.to_excel(writer, sheet_name=symbol, index=False)
            
            # Get the worksheet
            worksheet = writer.sheets[symbol]
            
            # Set column widths
            worksheet.column_dimensions['A'].width = 12  # Date
            worksheet.column_dimensions['B'].width = 10  # Open
            worksheet.column_dimensions['C'].width = 10  # High
            worksheet.column_dimensions['D'].width = 10  # Low
            worksheet.column_dimensions['E'].width = 10  # Close
            worksheet.column_dimensions['F'].width = 12  # Volume
            worksheet.column_dimensions['G'].width = 10  # Dividends
            worksheet.column_dimensions['H'].width = 10  # Stock Splits
            
            # Set date format for the date column
            for row in range(2, len(df_copy) + 2):  # Skip header row
                cell = worksheet[f"A{row}"]
                cell.number_format = 'yyyy-mm-dd'
            
            # Set number format for price columns (2 decimal places)
            for col in ['B', 'C', 'D', 'E']:  # Open, High, Low, Close columns
                for row in range(2, len(df_copy) + 2):  # Skip header row
                    cell = worksheet[f"{col}{row}"]
                    cell.number_format = '#,##0.00'
            
            # Set number format for volume column (whole numbers)
            for row in range(2, len(df_copy) + 2):  # Skip header row
                cell = worksheet[f"F{row}"]
                cell.number_format = '#,##0'

# Example usage
symbols = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'AMZN': 'Amazon',
    'JNJ': 'Johnson and Johnson',
    'WMT': 'Walmart',
    'TSLA': 'Tesla',
    'META': 'Meta',
    'SHOP': 'Shopify',
    'NVDA': 'Nvidia',
    'BA': 'Boeing',
    '^GSPC': 'S&P 500'
}

start_date = '2024-01-01'
end_date = '2025-02-07'

# Download data for all symbols
data = download_stock_data(symbols.keys(), start_date, end_date)

# Save data to Excel (change file extension)
save_stock_data(data, 'tech_stocks.xlsx')

# Print first few rows of each stock's data
for symbol in symbols:
    print(f"\n{symbols[symbol]} ({symbol}) Data:")
    print(data[symbol].head())
