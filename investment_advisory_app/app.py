from flask import Flask, request, jsonify
import pandas as pd
import yfinance as yf
import numpy as np
import talib as ta
from ta import add_all_ta_features
import requests

app = Flask(__name__)


# /tickers - GET: Fetches all the tickers from global exchanges.
# /historical_data - POST: Fetches historical data for a given stock symbol within a specified date range.
# /financial_ratios - POST: Fetches financial ratios for a given stock symbol.
# /balance_sheet - POST: Fetches balance sheet data for a given stock symbol.
# /cash_flow - POST: Fetches cash flow data for a given stock symbol.
# /technical_indicators - POST: Calculates and fetches technical indicators (SMA, RSI, MACD) for a given stock symbol within a specified date range.
# /all_technical_indicators - POST: Calculates and fetches all available technical indicators for a given stock symbol within a specified date range.


# Fetch tickers endpoint
@app.route('/tickers', methods=['GET'])
def fetch_tickers():
    try:
        print("Getting tickers...")
        api_key = "financialmodelingprep_apikey"
        base_url = "https://financialmodelingprep.com/api/v3/available-traded/list"
        params = {'apikey': api_key}
        response = requests.get(base_url, params=params)
        response.raise_for_status()  
        data = response.json()
        df = pd.json_normalize(data)
        return df.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch historical data endpoint
@app.route('/historical_data', methods=['POST'])
def fetch_historical_data():
    try:
        data = request.json
        symbol = data.get('symbol')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        print(f"Fetching {symbol} Stock Data...")
        data = yf.download(symbol, start=start_date, end=end_date)
        data['Symbol'] = symbol
        return data.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch financial ratios endpoint
@app.route('/financial_ratios', methods=['POST'])
def get_financial_ratios():
    try:
        data = request.json
        ticker = data.get('ticker')
        print(f"Getting {ticker} financial Ratios")
        ticker_object = yf.Ticker(ticker)
        quarterly_pl = ticker_object.quarterly_financials
        quarterly_pl = quarterly_pl.T
        
        yearly_pl = ticker_object.financials
        
        latest_sales = quarterly_pl["Total Revenue"].iloc[-1]
        latest_profit_after_tax = quarterly_pl["Net Income"].iloc[-1]
        yoy_sales_growth = (latest_sales - quarterly_pl["Total Revenue"].iloc[-5]) / quarterly_pl["Total Revenue"].iloc[-5] * 100
        latest_profit = quarterly_pl["Net Income"].iloc[-1]
        profit_3_quarters_ago = quarterly_pl["Net Income"].iloc[-4]
        yoy_profit_growth = (latest_profit - profit_3_quarters_ago) / profit_3_quarters_ago * 100
        sales_2_quarters_ago = quarterly_pl["Total Revenue"].iloc[-2]
        sales_growth = (latest_sales - sales_2_quarters_ago) / sales_2_quarters_ago * 100
        profit_2_quarters_ago = quarterly_pl["Net Income"].iloc[-2]
        profit_growth = (latest_profit - profit_2_quarters_ago) / profit_2_quarters_ago * 100
        operating_profit_latest = quarterly_pl["Operating Income"].iloc[-1]
        other_income_latest = quarterly_pl["Other Income Expense"].iloc[-1]
        ebitda_latest = quarterly_pl["EBITDA"].iloc[-1] + quarterly_pl['Reconciled Depreciation'].iloc[-1]
        depreciation_latest = quarterly_pl["Reconciled Depreciation"].iloc[-1]
        ebit_latest = quarterly_pl["EBIT"].iloc[-1]
        interest_latest = quarterly_pl["Interest Expense"].iloc[-1]
        profit_before_tax_latest = quarterly_pl['Pretax Income'].iloc[-1]
        tax_latest = quarterly_pl["Tax Provision"].iloc[-1]
        net_profit_latest = quarterly_pl["Net Income"].iloc[-1]
        gpm_latest = quarterly_pl['Gross Profit'].iloc[-1] / quarterly_pl['Total Revenue'].iloc[-1]
        opm_latest = quarterly_pl['Operating Income'].iloc[-1] / quarterly_pl['Total Revenue'].iloc[-1]
        npm_latest = quarterly_pl['Net Income'].iloc[-1] / quarterly_pl['Total Revenue'].iloc[-1]
        equity_capital_latest = quarterly_pl['Diluted EPS'].iloc[-1]
        
        data = {
            'Ticker': [ticker],
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
            'Net Profit': [net_profit_latest],
            'Gross Profit Margin': [gpm_latest],
            'Operating Profit Margin': [opm_latest],
            'Net Profit Margin': [npm_latest],
            'Equity Capital': [equity_capital_latest]            
        }
        df = pd.DataFrame(data)
        return df.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch balance sheet endpoint
@app.route('/balance_sheet', methods=['POST'])
def get_balance_sheet():
    try:
        data = request.json
        ticker = data.get('ticker')
        print(f"Getting {ticker} Balance Sheet")
        ticker_object = yf.Ticker(ticker)
        bals_sh = ticker_object.quarterly_balance_sheet
        bals_sh = bals_sh.T
        bals_sh["Ticker"] = ticker
        return bals_sh.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch cash flow endpoint
@app.route('/cash_flow', methods=['POST'])
def get_cash_flow():
    try:
        data = request.json
        ticker = data.get('ticker')
        print(f"Getting {ticker} Cash Flow")
        ticker_object = yf.Ticker(ticker)
        csf = ticker_object.quarterly_cash_flow 
        csf = csf.transpose()
        csf["Ticker"] = ticker
        return csf.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch technical indicators endpoint
@app.route('/technical_indicators', methods=['POST'])
def get_technical_indicators():
    try:
        data = request.json
        symbol = data.get('symbol')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        stock_data = yf.download(symbol, start=start_date, end=end_date)
        stock_data['SMA'] = ta.SMA(stock_data['Close'], timeperiod=14)
        stock_data['RSI'] = ta.RSI(stock_data['Close'], timeperiod=14)
        short_window = 12
        long_window = 26
        macd_line, signal_line, _ = ta.MACD(stock_data['Close'], fastperiod=short_window, slowperiod=long_window)
        stock_data['MACD'] = macd_line - signal_line
        return stock_data.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch all technical indicators endpoint
@app.route('/all_technical_indicators', methods=['POST'])
def get_all_technical_indicators():
    try:
        data = request.json
        symbol = data.get('symbol')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        stock_data = yf.download(symbol, start=start_date, end=end_date)
        all_TI = add_all_ta_features(stock_data, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True)
        all_TI["symbol"] = symbol
        return all_TI.to_json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
