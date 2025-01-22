import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def execute_trade(symbol, action, lot, price, slippage, take_profit, stop_loss):
    order_type = mt5.ORDER_BUY if action == 'BUY' else mt5.ORDER_SELL
    request = {
        'action': mt5.ORDER_BUY,
        'symbol': symbol,
        'volume': lot,
        'price': price,
        'slippage': slippage,
        'type': order_type,
        'tp': take_profit,
        'sl': stop_loss,
        'deviation': 20,
        'magic': 123456,
        'comment': 'Trade executed by AI',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to execute trade: {mt5.last_error()}")
    return result


def place_recovery_hedge(symbol, initial_trade_volume, hedge_price):
    hedge_volume = initial_trade_volume * 2
    slippage = 10
    request = {
        'action': mt5.ORDER_BUY_LIMIT if hedge_price > mt5.symbol_info_tick(symbol).bid else mt5.ORDER_SELL_LIMIT,
        'symbol': symbol,
        'volume': hedge_volume,
        'price': hedge_price,
        'slippage': slippage,
        'type': mt5.ORDER_BUY if hedge_price > mt5.symbol_info_tick(symbol).bid else mt5.ORDER_SELL,
        'deviation': 20,
        'magic': 123456,
        'comment': 'Recovery hedge order',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to place recovery hedge: {mt5.last_error()}")
    return result


def set_break_even_trailing_stop(symbol, position_id, trailing_stop_distance):
    position = mt5.positions_get(position_id=position_id)
    if not position:
        print("Position not found.")
        return
    
    current_price = mt5.symbol_info_tick(symbol).bid
    position_volume = position[0].volume
    
    new_sl = current_price - trailing_stop_distance
    request = {
        'action': mt5.ORDER_MODIFY,
        'symbol': symbol,
        'volume': position_volume,
        'price': current_price,
        'sl': new_sl,
        'tp': position[0].take_profit,
        'deviation': 20,
        'magic': 123456,
        'comment': 'Break-even trailing stop',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to set break-even trailing stop: {mt5.last_error()}")
    return result


def update_take_profit(symbol, position_id, new_take_profit):
    position = mt5.positions_get(position_id=position_id)
    if not position:
        print("Position not found.")
        return
    
    current_price = mt5.symbol_info_tick(symbol).bid
    position_volume = position[0].volume
    request = {
        'action': mt5.ORDER_MODIFY,
        'symbol': symbol,
        'volume': position_volume,
        'price': current_price,
        'sl': position[0].stop_loss,
        'tp': new_take_profit,
        'deviation': 20,
        'magic': 123456,
        'comment': 'Take profit updated',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to update take profit: {mt5.last_error()}")
    return result
