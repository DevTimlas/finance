# 1. Collect all the tickers from all global exhanges, save as table stocks using

import requests
import pandas as pd
import yfinance as yf
from questdb.ingress import Sender
import numpy as np
import talib as ta
from ta import add_all_ta_features

def fetch_tickers():
    try:
        print("getting tickers...")
        api_key = "financialmodelingprep_apikey" # jWGIkWgNiFf7mJynZvy5wHNrsd3w0qZw
        base_url = f"https://financialmodelingprep.com/api/v3/available-traded/list"
        params = {'apikey': api_key}
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        df = pd.json_normalize(data)
        return df
    except RequestException as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return []
        
# print(fetch_tickers().head())

# 2. Use yfinance to collect all historical data prices for past 30 years

# Download historical price data using Yahoo Finance
def fetch_historical_data(symbol, start_date, end_date):
    print(f"Fetching {symbol} Stock Data...")
    data = yf.download(symbol, start=start_date, end=end_date)
    data['Symbol'] = symbol
    return data

###### FUNDAMENTAL ANALYSIS #####

# 3. Get Yearly & Quaterly P&L data from yfinanace

def get_stock_ratios(ticker_f):
    try:
        print(f"Getting {ticker_f} financial Ratios")
        ticker = yf.Ticker(ticker_f)
        quarterly_pl = ticker.quarterly_financials
        quarterly_pl = quarterly_pl.T
        
        yearly_pl = ticker.financials
        print(quarterly_pl.columns)
        
        # 1. **Sales (Revenue) for the Latest Quarter**:
        latest_sales = quarterly_pl["Total Revenue"].iloc[-1]

        # 2. **Profit After Tax for the Latest Quarter**:
        latest_profit_after_tax = quarterly_pl["Net Income"].iloc[-1]

        # 3. **Year-Over-Year (YOY) Quarterly Sales Growth**:
        yoy_sales_growth = (latest_sales - quarterly_pl["Total Revenue"].iloc[-5]) / quarterly_pl["Total Revenue"].iloc[-5] * 100


        # 4. **Year-Over-Year (YOY) Quarterly Profit Growth**:
        latest_profit = quarterly_pl["Net Income"].iloc[-1]
        profit_3_quarters_ago = quarterly_pl["Net Income"].iloc[-4]
        yoy_profit_growth = (latest_profit - profit_3_quarters_ago) / profit_3_quarters_ago * 100

        # 5. **Sales Growth**:
        sales_2_quarters_ago = quarterly_pl["Total Revenue"].iloc[-2]
        sales_growth = (latest_sales - sales_2_quarters_ago) / sales_2_quarters_ago * 100


        # 6. **Profit Growth**:
        profit_2_quarters_ago = quarterly_pl["Net Income"].iloc[-2]
        profit_growth = (latest_profit - profit_2_quarters_ago) / profit_2_quarters_ago * 100
        # print(profit_growth)
                
        # 7. **Operating Profit for the Latest Quarter**:
        operating_profit_latest = quarterly_pl["Operating Income"].iloc[-1]
        # print(operating_profit_latest)

        # 8. **Other Income for the Latest Quarter**:
        other_income_latest = quarterly_pl["Other Income Expense"].iloc[-1]

        # 9. **EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization) for the Latest Quarter**:
        ebitda_latest = quarterly_pl["EBITDA"].iloc[-1] + quarterly_pl['Reconciled Depreciation'].iloc[-1]

        # 10. **Depreciation for the Latest Quarter**:
        depreciation_latest = quarterly_pl["Reconciled Depreciation"].iloc[-1]

        # 11. **EBIT (Earnings Before Interest and Taxes) for the Latest Quarter**:
        ebit_latest = quarterly_pl["EBIT"].iloc[-1]
        # print("Ebit lat", ebit_latest)


        # 12. **Interest Expense for the Latest Quarter**:
        interest_latest = quarterly_pl["Interest Expense"].iloc[-1]
        
        # 13. **Profit Before Tax for the Latest Quarter**:
        profit_before_tax_latest = quarterly_pl['Pretax Income'].iloc[-1]

        # 14. **Tax Expense for the Latest Quarter**:
        tax_latest = quarterly_pl["Tax Provision"].iloc[-1]

        # 15. **Extraordinary Items for the Latest Quarter**:
        # extraordinary_items_latest = quarterly_pl["Total Unusual Items"].iloc[-1]

        # 16. **Net Profit for the Latest Quarter**:
        net_profit_latest = quarterly_pl["Net Income"].iloc[-1]

        # 17. **Gross Profit Margin (GPM) for the Latest Quarter**:
        # gpm_latest = (latest_sales - quarterly_pl["Cost Of Revenue"].iloc[-1]) / latest_sales * 100
        gpm_latest = quarterly_pl['Gross Profit'].iloc[-1] / quarterly_pl['Total Revenue'].iloc[-1]

        # 18. **Operating Profit Margin (OPM) for the Latest Quarter**:
        # opm_latest = operating_profit_latest / latest_sales * 100
        opm_latest = quarterly_pl['Operating Income'].iloc[-1] / quarterly_pl['Total Revenue'].iloc[-1]

        # 19. **Net Profit Margin (NPM) for the Latest Quarter**:
        # npm_latest = net_profit_latest / latest_sales * 100
        npm_latest = quarterly_pl['Net Income'].iloc[-1] / quarterly_pl['Total Revenue'].iloc[-1]

        # 20. **Equity Capital for the Latest Quarter**:
        # equity_capital_latest = yearly_pl["Total Equity"].iloc[-1]
        equity_capital_latest = quarterly_pl['Diluted EPS'].iloc[-1]
        # print(equity_capital_latest)
        
        # 21
        Operating_profit_2quarters_back = quarterly_pl['Operating Income'].shift(2)
        print(Operating_profit_2quarters_back)
        
        # 22
        Operating_profit_3quarters_back = quarterly_pl['Operating Income'].shift(3)
        
        # 23
        Sales_2quarters_back = quarterly_pl['Total Revenue'].shift(2)
        
        # 24
        Sales_3quarters_back = quarterly_pl['Total Revenue'].shift(3)
        
        # 25
        Net_profit_2quarters_back = quarterly_pl['Net Income'].shift(2)
        
        # 26
        Net_profit_3quarters_back = quarterly_pl['Net Income'].shift(3)
        
        # 27
        Operating_profit_growth = quarterly_pl['Operating Income'].pct_change()
        
        # 28
        Last_result_date = quarterly_pl.index[-1]
        print(Last_result_date)

        
        # Creating a DataFrame
        data = {
            'Ticker': [ticker_f],
            'Latest Sales': [latest_sales],
            'Latest Profit After Tax': [latest_profit_after_tax],
            'YOY Sales Growth': [yoy_sales_growth],
            'YOY Profit Growth': [yoy_profit_growth],
            'Sales Growth': [sales_growth],
            'Profit Growth': [profit_growth],
            'Operating Profit': [operating_profit_latest],
            'Other Income': [other_income_latest],
            'EBITDA': [ebitda_latest],
            'Depreciation': [depreciation_latest],
            'EBIT': [ebit_latest],
            'Interest Expense': [interest_latest],
            'Profit Before Tax': [profit_before_tax_latest],
            'Tax Expense': [tax_latest],
            # 'Extraordinary Items': [extraordinary_items_latest],
            'Net Profit': [net_profit_latest],
            'Gross Profit Margin': [gpm_latest],
            'Operating Profit Margin': [opm_latest],
            'Net Profit Margin': [npm_latest],
            'Equity Capital': [equity_capital_latest]            
        }
        # print(data)

        df = pd.DataFrame(data)
        # print(df)

        return df
    except Exception as e:
        print("Error getting ratios", e)

    
def get_bals_sheet(ticker):
    print(f"Getting {ticker} Bals Sheet")
    ticker_object = yf.Ticker(ticker)
    bals_sh = ticker_object.quarterly_balance_sheet
    bals_sh = bals_sh.T
    bals_sh["Ticker"] = ticker
        
    # Convert DataFrame to be C-contiguous
    for col in bals_sh.columns:
        bals_sh[col] = np.ascontiguousarray(bals_sh[col])
    
    return bals_sh
    
def get_cash_flow(ticker):
    print(f"Getting {ticker} cash flow")
    ticker_object = yf.Ticker(ticker)
    csf = ticker_object.quarterly_cash_flow 
    csf = csf.transpose()
    csf["Ticker"] = ticker
    
    # Convert DataFrame to be C-contiguous
    for col in csf.columns:
        csf[col] = np.ascontiguousarray(csf[col])
    return csf
    
    
    
######### Technical Analysis ##########

# calculate SMA
def calculate_sma(df, window):
    return ta.SMA(df['Close'], timeperiod = window)

# calculate RSI
def calculate_rsi(df, window):
    return ta.RSI(df['Close'], timeperiod = window)

# calculate MACD
def calculate_macd(df, short_window, long_window):
    macd_line, signal_line, _ = ta.MACD(df['Close'], fastperiod=short_window, slowperiod=long_window)
    return macd_line - signal_line

    
def write_to_questdb(df, table_name):
    with Sender('localhost', 9009) as sender:
        sender.dataframe(df, table_name=table_name)
        sender.flush()
    
    
if __name__ == "__main__":
    start_date = "1994-01-01"
    end_date = "2024-01-01"
    # tickers = fetch_tickers()['symbol'].to_list()
    tickers = ["AAPL", "GOOG"]
    print("tickers", tickers[:5])
    window_sma = 14
    window_rsi = 14
    short_window = 12
    long_window = 26
    signal_window = 9
    
    for ticker in tickers[:]:
        stock_data = fetch_historical_data(ticker, start_date, end_date)
        write_to_questdb(stock_data, f"historical_data")
        # print(stock_data)
        
        stock_ratio = get_stock_ratios(ticker)
        write_to_questdb(stock_ratio, f"stock_ratio")
        # print(stock_ratio)
        
        balance_sheet = get_bals_sheet(ticker)
        write_to_questdb(balance_sheet, f"balance_sheet")
        # print(balance_sheet.head())
        
        cash_flow = get_cash_flow(ticker)
        write_to_questdb(cash_flow, f"cash_flow")
        # print(cash_flow)
        
        stock_data['SMA'] = calculate_sma(stock_data, window_sma)
        stock_data['RSI'] = calculate_rsi(stock_data, window_rsi)
        stock_data['MACD'] = calculate_macd(stock_data, short_window, long_window)
        write_to_questdb(stock_data, f"technical_indicators")

        all_TI = add_all_ta_features(stock_data, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True)
        all_TI["symbol"] = ticker
        write_to_questdb(all_TI, f"all_technical_indicators")
