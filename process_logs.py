# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 23:16:31 2021

@author: jonsnow
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Apr  2 11:57:36 2021

@author: jonsnow
"""

import json
import pandas as pd
import datetime
from binance.client import Client
import time
from time import sleep
from enum import Enum
from requests.exceptions import ReadTimeout

MAX_TRADES = 2
MAX_USD = 50
MAX_PERCENTAGE_ALLOCATION=30
usd_limit_mode = "constant"
#btc_to_spend = 0.001
folder_config_path = "config_files_binance_trader/"
binance_credentials_file_path = folder_config_path + "bn_c.json"
#coin_list_whitelist_file_path = folder_config_path + "coin_whitelist.txt"
#coin_list_blacklist_file_path = folder_config_path + "coin_blacklist.txt"
config_file_path = folder_config_path + "config.json"
path_logfile = "processed_signals_action_log.txt"
#list_model = "WHITELIST"
#list_model = "BLACKLIST"
positions_opened = 0
lines_count = 0

class Status_of_signal(Enum):
    NEW = 1
    SENT_ORDER = 2
    CANCELLED = 3
    SOLD_PROFIT = 4
    SOLD_STOPLOSS = 5
    DISMISSED = 6

def init_opened_orders_df():
    df = pd.DataFrame(columns=['coin', 'order'])
    df = df.set_index('coin')
    return df

def init_signals_df():
    result = pd.DataFrame(columns=['coin1', 'coin2', 'exchange_list',
                          'signal_direction', 'leverage',
                          'leverage_type', 'amount',  'entry', 
                          'take_profit', 'stop_loss',
                          'status', 'time_of_signal',
                          'orderId_profit', 'orderId_stop'
                          ])
    return result

def read_logs_file(path):
    with open(path, 'r') as f:
        lines = f.read().splitlines()
    return lines

def get_max_usd_spendable_total():
    return MAX_USD

def get_max_usd_per_coin():
    return get_max_usd_spendable_total() / MAX_TRADES

def get_dict_from_file_single_line(path):
    with open(path, 'r') as f:
        lines = f.read().splitlines()
    return json.loads(lines[0])

def get_binance_credentials(path):
    binance_credentials_dict = get_dict_from_file_single_line(path)
    return binance_credentials_dict["bn_k"], binance_credentials_dict["bn_p"]

def init_binance_clint_with_credentials_from_file(path):
    binance_credentials = get_binance_credentials(path)
    return Client(binance_credentials[0], binance_credentials[1])

def read_coin_list_from_txt_file(path):
    lines = []
    with open(path, 'r') as f:
        lines = f.read().splitlines()
    return lines

def check_if_new_line_added(lines):
    return (len(lines) > lines_count )

def read_new_line_from_logs_file(path):
    global lines_count
    lines = read_logs_file(path)
    last_line = ''
    if (check_if_new_line_added(lines)):
        last_line = lines[-1]
        lines_count = len(lines)
    return last_line


def get_coin_price_spot_last_price(coin1, coin2):
    return float(client.get_symbol_ticker(symbol=coin1 + coin2)['price'])


def get_coin_futures_last_price(coin1, coin2):
    return float(client.futures_ticker(symbol=coin1 + coin2)['lastPrice'])


def get_coin_price(coin1, coin2):
    return get_coin_price_spot_last_price(coin1, coin2)

def set_price(coin, base_price):
    return base_price / get_coin_price(coin)

def is_line_passes_filter(line):
    if (line == ''):
        return False
    line_dict = json.loads(line.replace("'", '"') )
    coin = line_dict['coin1']
    #if (coin in coins_blacklist):
    #    return False
#    if (list_model == "WHITELIST"):
#        if (not (coin in coins_whitelist)):
#            return False
#    if (not (coin in coins_whitelist)):
#        return False
    return True
    
def process_logs_file(path):
    line = read_new_line_from_logs_file(path)
    if (is_line_passes_filter(line) == False):
        return False
    line_dict = json.loads(line.replace("'", '"') )
    coin1 = line_dict['coin1']
    coin2 = line_dict['coin2']
    exchange_list = line_dict['exchange_list'] if 'exchange_list' in line_dict.keys() else 'Binance Futures'
    signal_direction = line_dict['signal_direction'] if 'signal_direction' in line_dict.keys() else 'long'
    leverage = int(float(line_dict['leverage'])) if 'leverage' in line_dict.keys() else None
    leverage_type = str(line_dict['leverage_type']).lower() if 'leverage_type' in line_dict.keys() else 'cross'
    amount = int(float(line_dict['amount'])) if 'amount' in line_dict.keys() else None
    entry = float(line_dict['entry']) if 'entry' in line_dict.keys() else float('nan')
    take_profit = float(line_dict['take_profit']) if 'take_profit' in line_dict.keys() else float('nan')
    stop_loss = float(line_dict['stop_loss']) if 'stop_loss' in line_dict.keys() else float('nan')
    
    if((amount == None) or (leverage == None)):
        leverage_type = 'cross'
    
    amount = 2 if amount == None else amount
    leverage = 2 if leverage == None else leverage
    
    status = Status_of_signal.NEW
    time_of_signal = pd.to_datetime(datetime.datetime.now())
    result_dict = {
         "coin1" : coin1,
         "coin2" : coin2,
         "exchange_list" : exchange_list,
         "signal_direction" : signal_direction,
         "leverage" : leverage,
         "leverage_type" : leverage_type,
         "amount" : amount,
         "entry" : entry,
         "take_profit" : take_profit,
         "stop_loss" : stop_loss,
         "status" : status,
         "time_of_signal" : time_of_signal
     }
    if (result_dict['coin1'] not in df_signals.index):
        df_signals.loc[result_dict['coin1']] = pd.Series(result_dict)

def process_df_signals_with_status_new(df_new_records ,verbose = 0):
    global df_closed_positions, df_signals, positions_opened
    for i in range(len(df_new_records)):
        row = df_new_records.iloc[i]
        current_price = get_coin_futures_last_price(row['coin1'], row['coin2'])
        max_time_before_signal = datetime.timedelta(days=1)
        if(row['time_of_signal'] - datetime.datetime.now() > max_time_before_signal):
            ####cancel signal and remove from df
            if (verbose >= 1):
                print("{}/{} pair coin signal has expired".format(row['coin1'], row['coin2']))
            continue
        if row['signal_direction'].lower() == "long":
            if(current_price >= row['take_profit']):
                ####cancel signal and remove from df
                if (verbose >= 1):
                    print("{}/{} pair coin signal has expired due to reaching target price before entry price".format(row['coin1'], row['coin2']))
                continue
            if(current_price < row['entry']):
                if (verbose >= 1):
                    print("{}/{} pair coin signal has reached entry price".format(row['coin1'], row['coin2']))
                if positions_opened < MAX_TRADES:
                    quantity = get_max_usd_per_coin() * row['amount'] / current_price  / 100
                    symbol = row['coin1'] + row['coin2']

                    
                    min_lot_size = float(client.get_symbol_info(symbol)['filters'][2]['minQty'])
                    quantity_new = min_lot_size * (int (quantity / min_lot_size) )
                    
                    
                    order = client.futures_create_order(
                                    symbol=symbol,
                                    side="BUY",
                                    type="MARKET",
                                    quantity=quantity_new)
                    print(order)
                    log_line =  '\n'.join(["position opened",
                                           "pair: {}/{}".format(row['coin1'], row['coin2']),
                                           "leverage: {}".format(row['leverage']),
                                           "{}% of the portfollio".format(row['amount']),
                                           "quantity: {}".format(quantity_new),
                                           "price entered: {}".format(current_price),
                                           "at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                           ])
                    print(log_line)
                    sleep(2)
                    order_buy = client.futures_create_order(
                                    symbol=symbol,
                                    side="SELL",
                                    type="TAKE_PROFIT",
                                    quantity=quantity_new,
                                    price=row['take_profit'],
                                    stopPrice=row['take_profit'])



                    order_sell = client.futures_create_order(
                                                        symbol=symbol,
                                                        side="SELL",
                                                        type="STOP_MARKET",
                                                        quantity=quantity_new,
                                                        stopPrice=row['stop_loss'])
                    save_purchase_to_log_file(path_logfile, log_line)
                    df_signals.loc[row['coin1'], 'orderId_profit'] = order_buy['orderId']
                    df_signals.loc[row['coin1'], 'orderId_stop'] = order_sell['orderId']
                    df_signals.loc[row['coin1'], 'status'] = Status_of_signal.SENT_ORDER
                    positions_opened += 1
                else:
                    log_line =  '\n'.join(["signal dismissed due to max limit of orders",
                                           "pair: {}/{}".format(row['coin1'], row['coin2']),
                                           "leverage: {}".format(row['leverage']),
                                           "{}% of the portfollio".format(row['amount']),
                                           "price entered: {}".format(current_price),
                                           "at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                           ])
                    print(log_line)
                    save_purchase_to_log_file(path_logfile, log_line)
                    df_signals.loc[row['coin1'], 'status'] = Status_of_signal.DISMISSED
        elif direction.lower() == 'short':
            ### TBD
            pass
                

def process_df_signals_with_status_sent_order(df_records ,verbose = 0):
    global df_closed_positions, df_signals, positions_opened
    for i in range(len(df_records)):
        row = df_records.iloc[i]
        current_price = get_coin_futures_last_price(row['coin1'], row['coin2'])
        direction = row['signal_direction']
        if direction.lower() == 'long':
            symbol = row['coin1'] + row['coin2']
            status_buy = client.futures_get_order(symbol=symbol,orderId=row['orderId_profit'])['status']
            status_sell = client.futures_get_order(symbol=symbol,orderId=row['orderId_stop'])['status']
            
            if (status_buy == 'FILLED'):
                client.futures_cancel_order(orderId=row['orderId_stop'], symbol=symbol)
                ####sell coin with profit and remove from df
                if (verbose >= 1):
                    print("{}/{} pair coin has reached target price!".format(row['coin1'], row['coin2']))
                log_line =  '\n'.join(["position closed",
                                       "pair: {}/{}".format(row['coin1'], row['coin2']),
                                       "leverage: {}".format(row['leverage']),
                                       "{}% of the portfollio".format(row['amount']),
                                       "price sold: {}".format(current_price),
                                       "at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                       ])
                print(log_line)
                save_purchase_to_log_file(path_logfile, log_line)
                df_signals.loc[row['coin1'], 'status'] = Status_of_signal.SOLD_PROFIT
                positions_opened -= 1
                continue
            elif status_sell == 'FILLED':
                client.futures_cancel_order(orderId=row['orderId_profit'], symbol=symbol)
                if (verbose >= 1):
                    print("{}/{} pair coin signal has reached stop loss price".format(row['coin1'], row['coin2']))
                log_line =  '\n'.join(["position closed",
                                       "pair: {}/{}".format(row['coin1'], row['coin2']),
                                       "leverage: {}".format(row['leverage']),
                                       "{}% of the portfollio".format(row['amount']),
                                       "price sold: {}".format(current_price),
                                       "at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                       ])
                print(log_line)
                save_purchase_to_log_file(path_logfile, log_line)
                df_signals.loc[row['coin1'], 'status'] = Status_of_signal.SOLD_STOPLOSS
                positions_opened -= 1
        elif direction.lower() == 'short':
            ### TBD
            pass
    df_closed_positions = pd.concat([df_closed_positions, df_signals[df_signals['status'] == Status_of_signal.SOLD_PROFIT].copy()], axis=0)
    df_closed_positions = pd.concat([df_closed_positions, df_signals[df_signals['status'] == Status_of_signal.SOLD_STOPLOSS].copy()], axis=0)
    df_signals = df_signals.drop(df_signals[df_signals['status'] == Status_of_signal.SOLD_PROFIT].index)
    df_signals = df_signals.drop(df_signals[df_signals['status'] == Status_of_signal.SOLD_STOPLOSS].index)


def process_df_signals(verbose = 1):
    df_new_records = df_signals[df_signals['status'] == Status_of_signal.NEW]
    df_sent_order_records = df_signals[df_signals['status'] == Status_of_signal.SENT_ORDER]
    process_df_signals_with_status_new(df_new_records ,verbose = verbose)
    process_df_signals_with_status_sent_order(df_sent_order_records ,verbose = verbose)

def save_purchase_to_log_file(path_logfile, log_line):
    file_object  = open(path_logfile, 'a')
    file_object.write(str(log_line) + '\n')
    file_object.write('\n')
    file_object.close()    

def init_loop(path):
    lines = read_logs_file(path)
    global lines_count
    lines_count = len(lines)

def main_loop(path):
    try:
        init_loop(path)
        while (True):
            try:
                process_logs_file(path)
                process_df_signals(verbose = 1)
                time.sleep(2)
            except ReadTimeout:
                print (ReadTimeout)
            except Exception as e:
                print(e)
                break
    except Exception as e:
        print(e)

#coins_whitelist = read_coin_list_from_txt_file(coin_list_whitelist_file_path)
#coins_blacklist = read_coin_list_from_txt_file(coin_list_blacklist_file_path)
#config_dict_raw = get_dict_from_file_single_line(config_file_path)
#MAX_TRADES, list_model, btc_to_spend, base_currency = config_dict_raw['MAX_TRADES'], config_dict_raw['list_model'], config_dict_raw['money_to_spend'], config_dict_raw['base_currency']
client = init_binance_clint_with_credentials_from_file(binance_credentials_file_path)

opened_orders_df = init_opened_orders_df()
df_signals = init_signals_df()
df_closed_positions = init_signals_df()

main_loop(path)