import MetaTrader5 as mt5
import json
from datetime import datetime, timedelta
from main import *
from warnings import filterwarnings
from agency_swarm import Agent, Agency, set_openai_key
from time import sleep

set_openai_key(openai_api_key)

filterwarnings('ignore')

timeframe = "1m" 
candles = 1000 
symbols = ["EURUSD"]  # Add more symbols if needed
print(f'Fetching data for {len(symbols)} symbols')

# Function to get historical data and other initial setups
def initialize_data():
    history_data = get_history_data(timeframe=timeframe, candles=candles, symbols=symbols)
    spreads = {symbol: get_spread(symbol) for symbol in symbols}
    margin_data = calculate_margin(symbols)
    acct_info = get_account_info()
    open_order = get_open_orders()
    deals_summary = get_deals_summary(datetime(2024, 1, 1), datetime.now())
    return history_data

def get_ai_trade_signal(symbol, current_price, data):
    trader = Agent(
        name="AI Trader",
        description="Responsible for client communication, task planning, and management.",
        instructions="You must converse with other agents to ensure complete task execution.",
        temperature=0.5,
        model='gpt-4o-mini'
    )
    
    agency = Agency([trader], shared_instructions='You are a part of an AI development agency for trading bot.\n\n')
    
    sys_prompt = f"""
        You are an AI trading assistant. Given the following details of a financial instrument, generate a trading signal.
        1. Symbol: {symbol}
        2. Current Price: {current_price}
        3. Historical 1m data {data}
        
        The output should include:
        1. Confidence Percentage
        2. Action (BUY/SELL)
        3. Take Profit Price
        
        Just return a dictionary and map the results
            'confidence' with Confidence Percentage, 
            'action' with Action
            'take_profit' with Take Profit Price
        No long explanation. We just need a simple dictionary in Python, not enclosed in string or quote!
        Don't forget to add the % to the confidence result.
        """

    res = (agency.get_completion(sys_prompt, yield_messages=False))
    return res

def execute_trade(symbol, action, lot, price, slippage, take_profit):
    order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot,
        'price': price,
        'slippage': slippage,
        'type': order_type,
        'tp': take_profit,
        'deviation': 20,
        'magic': 23400,
        'comment': 'Trade executed by AI',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN, # ORDER_FILLING_FOK,
    }

    print(f"Executing trade request: {request}")
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to execute trade: {result.retcode}, {mt5.last_error()}")
    else:
        print(f"Trade executed successfully: {result}")
    
    return result

def place_recovery_hedge(symbol, initial_trade_volume, hedge_price, action):
    order_type = mt5.ORDER_TYPE_BUY_STOP if action == 'BUY' else mt5.ORDER_TYPE_SELL_STOP
    request = {
        'action': mt5.TRADE_ACTION_PENDING,
        'symbol': symbol,
        'volume': initial_trade_volume,
        'price': hedge_price,
        'slippage': 10,
        'type': order_type,
        'deviation': 20,
        'magic': 23400,
        'comment': 'Recovery hedge order',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN, # ORDER_FILLING_FOK,
    }
    
    print(f"Placing recovery hedge request: {request}")
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to place recovery hedge: {mt5.last_error()}")
    else:
        print(f"Recovery hedge placed successfully: {result}")
    
    return result

def main():
    if not mt5.initialize():
        raise RuntimeError("MetaTrader5 initialization failed.")

    symbol = 'EURUSD'
    lot_size = 0.1
    slippage = 10
    min_confidence = 70
    
    while True:
        history_data = initialize_data()
        
        for symbol in symbols:
            current_price = mt5.symbol_info_tick(symbol).ask
            print(f'Current price for {symbol}: {current_price}')
            
            print('AI making prediction...')
            ai_prediction = get_ai_trade_signal(symbol, current_price, history_data)
            # print(ai_prediction)
            
            try:
                ai_prediction = eval(ai_prediction)  
            except Exception as e:
                print(f"Error parsing AI prediction: {e}")
                continue
            
            print(f'ai_prediction for {symbol}: {ai_prediction}')
            if ai_prediction and float(ai_prediction['confidence'].replace('%', '')) >= min_confidence:
                action = ai_prediction['action']
                take_profit = float(ai_prediction['take_profit'])

                print(f"Attempting trade: Symbol={symbol}, Action={action}, Lot Size={lot_size}, Price={current_price}, Slippage={slippage}, Take Profit={take_profit}")
                price = mt5.symbol_info_tick(symbol).ask
                result = execute_trade(symbol, action, lot_size, price, slippage, take_profit)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    hedge_price = current_price + 0.0010 if action == 'SELL' else current_price - 0.0010
                    hedge_action = 'BUY' if action == 'SELL' else 'SELL'
                    place_recovery_hedge(symbol, lot_size, hedge_price, hedge_action)
                    
                    hedge_take_profit = hedge_price + 0.0010 if hedge_action == 'BUY' else hedge_price - 0.0010
                    print(f"Hedge trade Buy/Sell Price: {hedge_price}")
                    print(f"Hedge trade TakeProfit: {hedge_take_profit}")
                else:
                    print(f"Failed to execute trade: {mt5.last_error()}")
        
        print("Sleeping until the next candlestick...")
        print('\n\n\n')
        print('*'*100)
        sleep(70)  # Sleep for 70 seconds to wait for the next candlestick

    mt5.shutdown()

if __name__ == "__main__":
    main()
