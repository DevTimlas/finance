import MetaTrader5 as mt5
import json
from datetime import datetime
from langchain import LLMChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from main import *
from warnings import filterwarnings

filterwarnings('ignore')

timeframe = "1m" 
candles = 500 
symbols = ["EURUSD", "GBPUSD"] # , "USDJPY", "USDCHF", "EURJPY", "GBPJPY"] # get_all_symbols() # 
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

def get_ai_trade_signal(symbol, current_price, data):
    llm = ChatOpenAI(temperature=0, model='gpt-4o-mini',
                 api_key=openai_api_key)  
    
    memory = ConversationBufferMemory(memory_key="ai_trade_signal", return_messages=True)
    
    sys_prompt = f"""
    You are an AI trading assistant. Given the following details of a financial instrument, generate a trading signal.
    1. Symbol: {symbol}
    2. Current Price: {current_price}
    3. Historical 1m data {data}
    
    The output should include:
    1. Confidence Percentage
    2. Action (BUY/SELL)
    3. Take Profit Price

    just return a dictionary and map the results
        confidence with Confidence Percentage, 
        action with Action
        take_profit with Take Profit Price
    no long explanation. we jsut need a simple dictionary in Python, not enclosed in string or whatever or quote!
    don't forget to add the % to the confidence result.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(sys_prompt),
        MessagesPlaceholder(variable_name="ai_trade_signal")
    ])
    
    conversation = LLMChain(llm=llm, prompt=prompt, memory=memory)
    print('AI....')
    
    response = conversation.invoke({"text": f"Generate a trade signal for {symbol} with current price {current_price}"})
    # print(response['text'])
    return json.loads(response['text'])

def execute_trade(symbol, action, lot, price, slippage, take_profit):
    order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot,
        'price': price,
        'slippage': slippage,
        'type': mt5.ORDER_TYPE_BUY,
        'tp': take_profit,
        'deviation': 20,
        'magic': 23400,
        'comment': 'Trade executed by AI',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN, # ORDER_FILLING_FOK,
    }

    
    result = mt5.order_send(request)
    # print(result.retcode, mt5.TRADE_RETCODE_DONE)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        # print(f"Failed to execute trade: {result.retcode}, {mt5.last_error()}")
        print("result:", result)
        print('*')
    return result

def place_recovery_hedge(symbol, initial_trade_volume, hedge_price, action):
    slippage = 10
    order_type = mt5.ORDER_TYPE_BUY_STOP if action == 'BUY' else mt5.ORDER_TYPE_SELL_STOP
    request = {
        'action': mt5.TRADE_ACTION_PENDING,
        'symbol': symbol,
        'volume': initial_trade_volume,
        'price': hedge_price,
        'slippage': slippage,
        'type': order_type,
        'deviation': 20,
        'magic': 23400,
        'comment': 'Recovery hedge order',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN, # ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to place recovery hedge: {mt5.last_error()}")
    return result

def main():
    if not mt5.initialize():
        raise RuntimeError("MetaTrader5 initialization failed.")
    
    symbol = 'EURUSD'
    lot_size = 0.1
    slippage = 10
    min_confidence = 70

    current_price = mt5.symbol_info_tick(symbol).ask # mt5.symbol_info_tick(symbol).bid
    point = mt5.symbol_info(symbol).point
    print('current price', current_price)
    # Get AI prediction using LangChain
    print('AI making prediction...')
    ai_prediction = get_ai_trade_signal(symbol, current_price, history_data)
    print('ai_prediction', ai_prediction)
    if ai_prediction and float(ai_prediction['confidence'].replace('%', '')) >= min_confidence:
        action = ai_prediction['action']
        take_profit = float(ai_prediction['take_profit'])

        
        # (symbol, action, lot, price, slippage, take_profit)
        price = mt5.symbol_info_tick(symbol).ask
        print(symbol, action, lot_size, price, slippage, take_profit)
        result = execute_trade(symbol, action, lot_size, price, slippage, take_profit)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            position_id = result.order
            print(f"Probability / Confidence %: {ai_prediction['confidence']}")
            print(f"Symbol: {symbol}")
            print(f"First trade Buy/Sell Price: {current_price}")
            print(f"First trade TakeProfit price: {take_profit}")
            
            hedge_price = current_price + 0.0010 if action == 'SELL' else current_price - 0.0010
            hedge_action = 'BUY' if action == 'SELL' else 'SELL'
            place_recovery_hedge(symbol, lot_size, hedge_price, hedge_action)
            
            hedge_take_profit = hedge_price + 0.0010 if hedge_action == 'BUY' else hedge_price - 0.0010
            print(f"Hedge trade Buy/Sell Price: {hedge_price}")
            print(f"Hedge trade TakeProfit: {hedge_take_profit}")
        else:
            print(f"Failed to execute trade: {mt5.last_error()}")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
