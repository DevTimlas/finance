import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime


#display all rows and column 
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


# Mapping of user input to MetaTrader 5 timeframe constants
timeframe_mapping = {
    "1m": mt5.TIMEFRAME_M1,  # for 1 minute
    "2m": mt5.TIMEFRAME_M2,  # for 2 minutes
    "3m": mt5.TIMEFRAME_M3,  # for 3 minutes
    "4m": mt5.TIMEFRAME_M4,  # for 4 minutes
    "5m": mt5.TIMEFRAME_M5,  # for 5 minutes
    "6m": mt5.TIMEFRAME_M6,  # for 6 minutes
    "10m": mt5.TIMEFRAME_M10,  # for 10 minutes
    "12m": mt5.TIMEFRAME_M12,  # for 12 minutes
    "15m": mt5.TIMEFRAME_M15,  # for 15 minutes
    "20m": mt5.TIMEFRAME_M20,  # for 20 minutes
    "30m": mt5.TIMEFRAME_M30,  # for 30 minutes
    "1h": mt5.TIMEFRAME_H1,  # for 1 hour
    "2h": mt5.TIMEFRAME_H2,  # for 2 hours
    "3h": mt5.TIMEFRAME_H3,  # for 3 hours
    "4h": mt5.TIMEFRAME_H4,  # for 4 hours
    "6h": mt5.TIMEFRAME_H6,  # for 6 hours
    "8h": mt5.TIMEFRAME_H8,  # for 8 hours
    "12h": mt5.TIMEFRAME_H12,  # for 12 hours
    "1d": mt5.TIMEFRAME_D1,  # for 1 day
    "1w": mt5.TIMEFRAME_W1,  # for 1 week
    "1mn": mt5.TIMEFRAME_MN1,  # for 1 month
}

uname = 84737871
passw = 'S@4aGgAe'
serv = 'MetaQuotes-Demo'

if mt5.initialize(login=uname, password=passw, server=serv):
    print("Trading Bot Starting")
    # Login to MT5
    if mt5.login(login=uname, password=passw, server=serv):
        print("Trading Bot Logged in and Ready to Go!")
        # return True
    else:
        print("Login Fail")
        quit()
        # return PermissionError



def get_history_data(timeframe, candles, symbols):
    if timeframe not in timeframe_mapping:
        print("Invalid timeframe. Please enter a valid timeframe.")
        return None

    selected_timeframe = timeframe_mapping[timeframe]
    all_data = []

    for symbol in symbols:
        history_data = pd.DataFrame(mt5.copy_rates_from_pos(symbol, selected_timeframe, 0, candles))
        if history_data.empty:
            print(f"No data for symbol {symbol}")
            continue
        
        history_data['time'] = pd.to_datetime(history_data['time'], unit='s')  # Convert timestamp to readable format
        history_data = history_data.drop('real_volume', axis=1)
        history_data['symbol'] = symbol  # Add the symbol column
        all_data.append(history_data)
    
    if not all_data:
        return pd.DataFrame()  # Return an empty DataFrame if no data was collected

    # Concatenate all dataframes into a single dataframe
    combined_data = pd.concat(all_data, ignore_index=True)
    return combined_data


def get_spread(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found")
        return None
    spread = symbol_info.spread
    return spread


# Function to retrieve all open orders from MT5
def get_open_orders():
    orders = mt5.orders_get()
    order_array = []
    for order in orders:
        order_array.append(order[0])
    return order_array

def get_all_symbols():
    symbols = mt5.symbols_get()
    return [symbol.name for symbol in symbols]

def calculate_margin(symbols, lot=0.1):
    action = mt5.ORDER_TYPE_BUY
    print("Symbols to check margin:", symbols)
    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            # print(symbol, "not found, skipped")
            continue
        if not symbol_info.visible:
            # print(symbol, "is not visible, trying to switch on")
            if not mt5.symbol_select(symbol, True):
                # print(f"symbol_select({symbol}) failed, skipped")
                continue
        ask = mt5.symbol_info_tick(symbol).ask
        margin = mt5.order_calc_margin(action, symbol, lot, ask)
        if margin is not None:
            print(f"   {symbol} buy {lot} lot margin: {margin}")
        else:
            print("order_calc_margin failed: error code =", mt5.last_error())

def get_account_info():
    account_info = mt5.account_info()
    account_info_dict = account_info._asdict()
    relevant_info = {
        'Balance': account_info_dict.get('balance'),
        'Equity': account_info_dict.get('equity'),
        'Free Margin': account_info_dict.get('margin_free')
    }
    
    # Convert to DataFrame
    df = pd.DataFrame(list(relevant_info.items()), columns=['property', 'value'])
    return df

def get_deals_summary(from_date, to_date):
    results = {}
    deals = mt5.history_deals_get(from_date, to_date, group="*GBP*, *EUR*, *USD*")
    if deals is None:
        print(f"No deals with group=\*GBP*\*EUR*\*USD*\", error code={mt5.last_error()}")
        results['deals'] = pd.DataFrame()
    else:
        print(f"history_deals_get({from_date}, {to_date}, group=\"*GBP*\") = {len(deals)}")
        results['deals'] = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        results['deals']['time'] = pd.to_datetime(results['deals']['time'], unit='s')

    return results
    

def main():
    timeframe = "1m" 
    candles = 10000 
    symbols = get_all_symbols() # ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURJPY", "GBPJPY"]
    print(f'fetching data for {len(symbols)} symbols')
    from_date = datetime(2024, 1, 1)
    to_date = datetime.now()

    # Retrieve historical data for multiple symbols
    history_data = get_history_data(timeframe=timeframe, candles=candles, symbols=symbols)

    # Retrieve spreads for each symbol
    spreads = {symbol: get_spread(symbol) for symbol in symbols}

    # Calculate margin for each symbol
    margin_data = calculate_margin(symbols)

    # Retrieve account information
    acct_info = get_account_info()

    # Retrieve open orders
    open_order = get_open_orders()

    # Retrieve Historic Orderss
    deals_summary = get_deals_summary(from_date, to_date)
    

    return history_data, margin_data, acct_info, deals_summary, open_order


history_data, margin_data, acct_info, deals_summary, open_order = main()

print('margin data: ', margin_data)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('Acct Info: ', acct_info)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('history data: ', history_data.head())
print('*'*100)
print('\n\n\n\n\n\n\n')
print('open order: ', open_order)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('deals summary: ', deals_summary)
print('*'*100)