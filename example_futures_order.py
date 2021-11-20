# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 19:31:28 2021

@author: jonsnow
"""

from time import sleep


def adjust_leverage(symbol, client):
    client.futures_change_leverage(symbol=symbol, leverage=10)

def adjust_margintype(symbol, client):
    client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')


symbol="OMGUSDT"
quantity = 0.5

client.futures_change_leverage(symbol=symbol, leverage=6)
try:
    client.futures_change_margin_type(symbol=symbol, marginType='CROSSED')
except:
    pass



quantity * (1 - 0.01 * 0.04)


client.futures_create_order(
                                    symbol=symbol,
                                    side="BUY",
                                    type="MARKET",
                                    quantity=0.5)
sleep(5)
client.futures_create_order(
                                    symbol=symbol,
                                    side="SELL",
                                    type="TAKE_PROFIT",
                                    quantity=0.5,
                                    price=13.8,
                                    stopPrice=12.1)

print(client.futures_account_balance())

print(client.get_margin_account())



{'orderId': 13122839479,
 'symbol': 'OMGUSDT',
 'status': 'NEW',
 'clientOrderId': '5NcfwCNzndR3YTb2HuRVzJ',
 'price': '0',
 'avgPrice': '0.00000',
 'origQty': '0.5',
 'executedQty': '0',
 'cumQty': '0',
 'cumQuote': '0',
 'timeInForce': 'GTC',
 'type': 'MARKET',
 'reduceOnly': False,
 'closePosition': False,
 'side': 'BUY',
 'positionSide': 'BOTH',
 'stopPrice': '0',
 'workingType': 'CONTRACT_PRICE',
 'priceProtect': False,
 'origType': 'MARKET',
 'updateTime': 1636739786673}




order_buy = client.futures_create_order(
                                    symbol=symbol,
                                    side="SELL",
                                    type="TAKE_PROFIT",
                                    quantity=0.5,
                                    price=13.8,
                                    stopPrice=13.8)



order_sell = client.futures_create_order(
                                    symbol=symbol,
                                    side="SELL",
                                    type="STOP_MARKET",
                                    quantity=0.5,
                                    stopPrice=11.95)

client.futures_get_order(symbol=symbol,orderId=order_sell['orderId'])


status_buy = client.futures_get_order(symbol=symbol,orderId=order_buy['orderId'])['status']
status_sell = client.futures_get_order(symbol=symbol,orderId=order_sell['orderId'])['status']

while ((status_buy != "FILLED") and (status_sell != "FILLED")):
    status_buy = client.futures_get_order(symbol=symbol,orderId=order_buy['orderId'])['status']
    status_sell = client.futures_get_order(symbol=symbol,orderId=order_sell['orderId'])['status']
    
    if (status_buy == 'FILLED'):
        client.futures_cancel_order(orderId=order_sell['orderId'], symbol=symbol)
    elif status_sell == 'FILLED':
        client.futures_cancel_order(orderId=order_buy['orderId'], symbol=symbol)
    
    sleep(2)


pd.DataFrame(client.futures_funding_rate()).sort_values(by="fundingRate")