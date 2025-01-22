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

# if not mt5.initialize():
#     print("Initialization failed")
#     mt5.shutdown()

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

def get_history_data1(timeframe, candles, symbol="EURUSD"):
    if timeframe not in timeframe_mapping:
        print("Invalid timeframe. Please enter a valid timeframe.")
        return None

    selected_timeframe = timeframe_mapping[timeframe]
    history_data = pd.DataFrame(mt5.copy_rates_from_pos(symbol, selected_timeframe, 0, candles))
    history_data['time'] = pd.to_datetime(history_data['time'], unit='s')  # Convert timestamp to readable format
    history_data = history_data.drop('real_volume', axis=1)
    return history_data


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


def get_all_symbols():
    symbols = mt5.symbols_get()
    return [symbol.name for symbol in symbols]

# Function to retrieve all open orders from MT5
def get_open_orders():
    orders = mt5.orders_get()
    order_array = []
    for order in orders:
        order_array.append(order[0])
    return order_array


# Function to retrieve all open positions
def get_open_positions():
    # Get position objects
    positions = mt5.positions_get()
    # Return position objects
    return positions

def get_account_currency():
    """Get the currency of the trading account."""
    account_currency = mt5.account_info().currency
    print("Account currency:", account_currency)
    return account_currency

def calculate_margin(symbols, lot=0.1):
    """Calculate and print margin for a list of symbols."""
    action = mt5.ORDER_TYPE_BUY
    print("Symbols to check margin:", symbols)
    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(symbol, "not found, skipped")
            continue
        if not symbol_info.visible:
            print(symbol, "is not visible, trying to switch on")
            if not mt5.symbol_select(symbol, True):
                print(f"symbol_select({symbol}) failed, skipped")
                continue
        ask = mt5.symbol_info_tick(symbol).ask
        margin = mt5.order_calc_margin(action, symbol, lot, ask)
        if margin is not None:
            print(f"   {symbol} buy {lot} lot margin: {margin} {get_account_currency()}")
        else:
            print("order_calc_margin failed: error code =", mt5.last_error())

def get_account_info():
    """Retrieve and return account information as a DataFrame."""
    account_info = mt5.account_info()
    account_info_dict = account_info._asdict()
    # Balance / Equity / Free Margin
    relevant_info = {
        'Balance': account_info_dict.get('balance'),
        'Equity': account_info_dict.get('equity'),
        'Free Margin': account_info_dict.get('margin_free')
    }
    
    # Convert to DataFrame
    df = pd.DataFrame(list(relevant_info.items()), columns=['property', 'value'])
    return df


def get_deals_summary(from_date, to_date, position_id=None):
    """
    Retrieves and processes historical deals based on specified criteria.
    
    Parameters:
    - from_date (datetime): Start date for retrieving deals.
    - to_date (datetime): End date for retrieving deals.
    - position_id (int, optional): Position ID to filter deals. If None, retrieves deals for all criteria.
    
    Returns:
    - dict: A dictionary containing DataFrames for deals based on different criteria.
    """
    
    results = {}
    
    # 1. Get deals for symbols containing "GBP" within the specified interval
    deals_gbp = mt5.history_deals_get(from_date, to_date, group="*GBP*")
    if deals_gbp is None:
        print(f"No deals with group=\"*GBP*\", error code={mt5.last_error()}")
        results['deals_gbp'] = pd.DataFrame()
    else:
        print(f"history_deals_get({from_date}, {to_date}, group=\"*GBP*\") = {len(deals_gbp)}")
        results['deals_gbp'] = pd.DataFrame(list(deals_gbp), columns=deals_gbp[0]._asdict().keys())
        results['deals_gbp']['time'] = pd.to_datetime(results['deals_gbp']['time'], unit='s')
    
    # 2. Get deals for symbols containing neither "EUR" nor "GBP"
    deals_no_eur_gbp = mt5.history_deals_get(from_date, to_date, group="*,!*EUR*,!*GBP*")
    if deals_no_eur_gbp is None:
        print(f"No deals, error code={mt5.last_error()}")
        results['deals_no_eur_gbp'] = pd.DataFrame()
    else:
        print(f"history_deals_get({from_date}, {to_date}, group=\"*,!*EUR*,!*GBP*\") = {len(deals_no_eur_gbp)}")
        results['deals_no_eur_gbp'] = pd.DataFrame(list(deals_no_eur_gbp), columns=deals_no_eur_gbp[0]._asdict().keys())
        results['deals_no_eur_gbp']['time'] = pd.to_datetime(results['deals_no_eur_gbp']['time'], unit='s')
    
    # 3. Get all deals related to the specified position ID
    if position_id is not None:
        position_deals = mt5.history_deals_get(position=position_id)
        if position_deals is None:
            print(f"No deals with position #{position_id}")
            print(f"error code = {mt5.last_error()}")
            results['position_deals'] = pd.DataFrame()
        else:
            print(f"Deals with position id #{position_id}: {len(position_deals)}")
            results['position_deals'] = pd.DataFrame(list(position_deals), columns=position_deals[0]._asdict().keys())
            results['position_deals']['time'] = pd.to_datetime(results['position_deals']['time'], unit='s')
    
    return results


def main():
    timeframe = "1m"  # input("Enter the timeframe for candles (e.g., 1m, 1h, 1d, 1w, 1mn): ").lower()
    candles = 10000  # int(input("Trade Duration (number of candles): "))
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURJPY", "GBPJPY"]  # List of symbols to extract
    from_date = datetime(2020, 1, 1)
    to_date = datetime.now()

    # Retrieve historical data for multiple symbols
    history_data = get_history_data(timeframe=timeframe, candles=candles, symbols=symbols)

    # Retrieve spreads for each symbol
    spreads = {symbol: get_spread(symbol) for symbol in symbols}

    # Retrieve all available symbols
    all_symbols = get_all_symbols()

    # Retrieve account currency
    account_currency = get_account_currency()

    # Calculate margin for each symbol
    margin_data = calculate_margin(symbols)

    # Retrieve account information
    acct_info = get_account_info()

    deals_summary = get_deals_summary(from_date, to_date)

    position_id = 2688315443
    position_deals_summary = get_deals_summary(from_date, to_date, position_id=position_id)
    

    return history_data, spreads, all_symbols, account_currency, margin_data, acct_info, deals_summary, position_deals_summary



# Shutdown MetaTrader 5 connection
# mt5.shutdown()

print('open orders: ', get_open_orders())
print('*'*100)
print('\n\n\n\n\n\n\n')
print('open positions: ', get_open_positions())
print('*'*100)
print('\n\n\n\n\n\n\n')
# history_data, spread, all_symbols = main()
history_data, spread, all_symbols, account_currency, margin_data, acct_info, deals_summary, position_deals_summary = main()

print("data \n", history_data.head())
print('*'*100)
print('\n\n\n\n\n\n\n')
print("all symbols\n :", all_symbols)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('Acct currency: ', account_currency)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('margin data: ', margin_data)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('Acct Info: ', acct_info)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('size of the extracted data: ', history_data.shape)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('Deal Summary: ', deals_summary)
print('*'*100)
print('\n\n\n\n\n\n\n')
print('Position deals summary: ', position_deals_summary)
print('*'*100)
print('\n\n\n\n\n\n\n')

print('\n\n\n\n\n\n\n')
print('sample data')
print(history_data.head(10))
print(history_data.sample(10))
print(history_data.tail(10))