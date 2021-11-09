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
from enum import Enum

#MAX_TRADES = 5
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

def init_opened_orders_df():
    df = pd.DataFrame(columns=['coin', 'order'])
    df = df.set_index('coin')
    return df

def init_signals_df():
    result = pd.DataFrame(columns=['coin1', 'coin2', 'exchange_list',
                          'signal_direction', 'leverage', 'amount',
                          'entry', 'take_profit', 'stop_loss',
                          'status', 'time_of_signal'
                          ])
    return result

def read_logs_file(path):
    with open(path, 'r') as f:
        lines = f.read().splitlines()
    return lines

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

def get_coin_price(coin1, coin2):
    return float(client.get_symbol_ticker(symbol=coin1 + coin2)['price'])


def get_coin_futures_last_price(coin1, coin2):
    return float(client.futures_ticker(symbol=coin1 + coin2)['lastPrice'])


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

def place_market_order_binance(coin, side, quantity):
#    print(quantity)
#    order = client.create_test_order(
    order = client.create_order(
            symbol=coin + base_currency,
            side=side,
            type='MARKET',
            quantity="{:.3f}".format(quantity)
            )
    return order

def proceed_with_buy_order(coin):
    global positions_opened
    min_lot_size = float(client.get_symbol_info(coin + base_currency)['filters'][2]['minQty'])
    newprice = set_price(coin, btc_to_spend)
    newprice = min_lot_size * (int (newprice / min_lot_size) )
    order = place_market_order_binance(coin, "BUY", newprice)
    print("sent BUY order for pair {}. quantity {}".format(coin + base_currency, "{:.3f}".format(newprice)))
    opened_orders_df.loc[coin] = ['BUY']
    positions_opened += 1

def proceed_with_sell_order(coin):
    global positions_opened, opened_orders_df
    min_lot_size = float(client.get_symbol_info(coin+base_currency)['filters'][2]['minQty'])
    newprice = set_price(coin, 0.997 * btc_to_spend)
    newprice = min_lot_size * (int (newprice / min_lot_size) )
    order = place_market_order_binance(coin, "SELL", newprice)
    print("sent SELL order for pair {}. quantity {}".format(coin + base_currency, "{:.3f}".format(newprice)))
    opened_orders_df = opened_orders_df.drop(labels=[coin])
    positions_opened -= 1
    
def process_logs_file(path):
    line = read_new_line_from_logs_file(path)
    if (is_line_passes_filter(line) == False):
        return False
    line_dict = json.loads(line.replace("'", '"') )
    coin1 = line_dict['coin1']
    coin2 = line_dict['coin2']
    exchange_list = line_dict['exchange_list'] if 'exchange_list' in line_dict.keys() else 'Binance Futures'
    signal_direction = line_dict['signal_direction'] if 'signal_direction' in line_dict.keys() else 'long'
    leverage = int(float(line_dict['leverage'])) if 'leverage' in line_dict.keys() else 2
    amount = int(float(line_dict['amount'])) if 'amount' in line_dict.keys() else 2
    entry = float(line_dict['entry']) if 'entry' in line_dict.keys() else float('nan')
    take_profit = float(line_dict['take_profit']) if 'take_profit' in line_dict.keys() else float('nan')
    stop_loss = float(line_dict['stop_loss']) if 'stop_loss' in line_dict.keys() else float('nan')
    
    status = Status_of_signal.NEW
    time_of_signal = pd.to_datetime(datetime.datetime.now())
    result_dict = {
         "coin1" : coin1,
         "coin2" : coin2,
         "exchange_list" : exchange_list,
         "signal_direction" : signal_direction,
         "leverage" : leverage,
         "amount" : amount,
         "entry" : entry,
         "take_profit" : take_profit,
         "stop_loss" : stop_loss,
         "status" : status,
         "time_of_signal" : time_of_signal
     }
    if (result_dict['coin1'] not in df_signals.index):
        df_signals.loc[result_dict['coin1']] = pd.Series(result_dict)
#    if ((signal == 'BUY' ) and (response == 'X_TIME_PASSED') and (positions_opened < MAX_TRADES) and (coin not in opened_orders_df.index)):
#        proceed_with_buy_order(coin)
#    elif ((signal == 'SELL' ) and (response == 'X_TIME_PASSED') and (coin in opened_orders_df.index)):
#        proceed_with_sell_order(coin)

def process_df_signals_with_status_new(df_new_records ,verbose = 0):
    for i in range(len(df_new_records)):
        row = df_new_records.iloc[i]
        current_price = get_coin_futures_last_price(row['coin1'], row['coin2'])
        max_time_before_signal = datetime.timedelta(days=1)
        if(row['time_of_signal'] - datetime.datetime.now() > max_time_before_signal):
            ####cancel signal and remove from df
            if (verbose >= 1):
                print("{}/{} pair coin signal has expired".format(row['coin1'], row['coin2']))
            continue
        if(current_price >= row['take_profit']):
            ####cancel signal and remove from df
            if (verbose >= 1):
                print("{}/{} pair coin signal has expired".format(row['coin1'], row['coin2']))
            continue
        if(current_price < row['entry']):
            if (verbose >= 1):
                print("{}/{} pair coin signal has reached entry price".format(row['coin1'], row['coin2']))
            log_line =  '\n'.join(["position opened",
                                   "pair: {}/{}".format(row['coin1'], row['coin2']),
                                   "leverage: {}".format(row['leverage']),
                                   "{}% of the portfollio".format(row['amount']),
                                   "price entered: {}".format(current_price),
                                   "at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                   ])
            print(log_line)
            save_purchase_to_log_file(path_logfile, log_line)
            df_signals.loc[row['coin1'], 'status'] = Status_of_signal.SENT_ORDER

def process_df_signals(verbose = 1):
    df_new_records = df_signals[df_signals['status'] == Status_of_signal.NEW]
    process_df_signals_with_status_new(df_new_records ,verbose = verbose)
#    for i in range(len(df_new_records)):
#        row = df_new_records.iloc[i]
#        current_price = get_coin_price(row['coin1'])
#        max_time_before_signal = datetime.timedelta(days=1)
#        if(row['time_of_signal'] - datetime.datetime.now() > max_time_before_signal):
#            ####cancel signal and remove from df
#            if (verbose >= 1):
#                print("{}/{} pair coin signal has expired".format(row['coin1'], row['coin2']))
#            continue
#        if(current_price >= row['take_profit']):
#            ####cancel signal and remove from df
#            if (verbose >= 1):
#                print("{}/{} pair coin signal has expired".format(row['coin1'], row['coin2']))
#            continue
#        if(current_price < row['entry']):
#            if (verbose >= 1):
#                print("{}/{} pair coin signal has reached entry price".format(row['coin1'], row['coin2']))
#            log_line =  '\n'.join(["position opened",
#                                   "pair: {}/{}".format(row['coin1'], row['coin2']),
#                                   "leverage: {}".format(row['leverage']),
#                                   "{}% of the portfollio".format(row['amount']),
#                                   "price entered: {}".format(current_price),
#                                   "at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#                                   ])
#            print(log_line)
#            save_purchase_to_log_file(path_logfile, log_line)
#            df_signals.loc[row['coin1'], 'status'] = Status_of_signal.SENT_ORDER
        

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
            process_logs_file(path)
            time.sleep(2)
    except Exception as e:
        print(e)

coins_whitelist = read_coin_list_from_txt_file(coin_list_whitelist_file_path)
coins_blacklist = read_coin_list_from_txt_file(coin_list_blacklist_file_path)
config_dict_raw = get_dict_from_file_single_line(config_file_path)
MAX_TRADES, list_model, btc_to_spend, base_currency = config_dict_raw['MAX_TRADES'], config_dict_raw['list_model'], config_dict_raw['money_to_spend'], config_dict_raw['base_currency']
client = init_binance_clint_with_credentials_from_file(binance_credentials_file_path)

opened_orders_df = init_opened_orders_df()
df_signals = init_signals_df()