import yfinance as yf
import pandas as pd
from numba import njit
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
import numpy as np
import ta

# Define the SQLite database connection
DATABASE_URL = 'sqlite:///technical_data.db'
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define the TechnicalIndicator model
class TechnicalIndicator(Base):
    __tablename__ = 'technical_indicators'
    id = Column(Integer, primary_key=True, index=True)
    asset = Column(String, index=True)
    timestamp = Column(TIMESTAMP, index=True)
    indicator_name = Column(String)
    value = Column(Float)

# Download historical price data using Yahoo Finance
def fetch_historical_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date)
    return data

# Calculate SMA using numba for acceleration
@njit
def calculate_sma(prices, window):
    sma_values = []
    for i in range(window - 1, len(prices)):
        sma = prices[i - window + 1:i + 1].sum() / window
        sma_values.append(sma)
    return sma_values

# Calculate RSI using numba for acceleration
@njit
def calculate_rsi(prices, window):
    rsi_values = [0] * (len(prices) - window + 1)
    for i in range(window, len(prices)):
        avg_gain = 0
        avg_loss = 0
        for j in range(i - window + 1, i):
            change = prices[j + 1] - prices[j]
            if change > 0:
                avg_gain += change
            else:
                avg_loss += abs(change)
        avg_gain /= window
        avg_loss /= window
        if avg_loss == 0:
            rs = 1
        else:
            rs = avg_gain / avg_loss
        rsi_values[i - window] = 100 - (100 / (1 + rs))
    return rsi_values
    
    
# Calculate Exponential Moving Average (EMA) using numba for acceleration
@njit
def calculate_ema(prices, window):
    """EMA = (Price(t) * k) + (EMA(y) * (1 – k))
        Where:
            Price(t) is the price at time (t)
            EMA(y) is the previous period’s EMA
            k is the smoothing constant, which is typically set at 2/(n+1) where n is the number of periods for the EMA"""
    ema_values = [0] * len(prices)
    ema_values = np.asarray(ema_values)
    multiplier = 2 / (window + 1)
    ema_values[window - 1] = prices[:window].mean()
    for i in range(window, len(prices)):
        ema_values[i] = (prices[i] - ema_values[i - 1]) * multiplier + ema_values[i - 1]
    return ema_values

# Calculate MACD using numba for acceleration
@njit
def calculate_macd1(prices, short_window, long_window, signal_window):
    short_ema = calculate_ema(prices, short_window)
    long_ema = calculate_ema(prices, long_window)
    macd_line = short_ema - long_ema
    signal_line = calculate_ema(macd_line, signal_window)
    return macd_line - signal_line
    
# Numba-accelerated function to calculate moving average convergence divergence (MACD)
@njit
def calculate_macd2(close, window_fast, window_slow, signal_window):
    macd = calculate_ema(close, window_fast) - calculate_ema(close, window_slow)
    # print("macd", macd)
    # print(calculate_ema(close, window_fast))
    # print(calculate_ema(close, window_slow))
    signal = calculate_ema(macd[window_slow - window_fast:], signal_window)
    histogram = macd[window_slow - window_fast:] - signal
    return macd, signal, histogram
    
def calculate_macd(df):
    macd_object = ta.trend.MACD(df)
    # data['MACD'] = macd_object.macd() # macd line
    # data['MACD_Signal'] = macd_object.macd_signal() # signal line
    # data['MACD_Diff'] = macd_object.macd_diff() # histogram
    return macd_object.macd()


# Store technical indicators in the database
def store_technical_indicators(asset, timestamps, indicator_name, values):
    session = Session()
    for i in range(len(timestamps)):
        indicator = TechnicalIndicator(
            asset=asset,
            timestamp=timestamps[i],
            indicator_name=indicator_name,
            value=values[i]
        )
        session.add(indicator)
    session.commit()
    session.close()

# Main function
def main():
    symbols = ['AAPL', 'AMZN']
    start_date = '2022-01-01'
    end_date = '2022-12-31'
    window_sma = 14
    window_rsi = 14
    short_window = 12
    long_window = 26
    signal_window = 9
    
    for symbol in symbols:

        # Fetch historical price data
        data = fetch_historical_data(symbol, start_date, end_date)

        # Calculate SMA
        sma_values = calculate_sma(data['Close'].values, window_sma)
        store_technical_indicators(symbol, data.index[window_sma - 1:], 'SMA', sma_values)

        # Calculate RSI
        rsi_values = calculate_rsi(data['Close'].values, window_rsi)
        store_technical_indicators(symbol, data.index[window_rsi:], 'RSI', rsi_values)

        # Calculate MACD
        # macd_values = calculate_macd(data['Close'].values, short_window, long_window, signal_window) # old
        macd_values = calculate_macd(data['Close'])
        print(macd_values)
        store_technical_indicators(symbol, data.index[long_window + signal_window - 1:], 'MACD', macd_values)
        # store_technical_indicators(symbol, data.index[long_window + signal_window - 1:], 'MACD', macd_values[0]) # old

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    main()

