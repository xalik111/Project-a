import datetime
import logging
import threading
from threading import Timer

import numpy as np
from binance.client import Client
from binance.enums import *

from .models import Users, Orders

client = Client('key1', 'key2')


def create_order(user_id, date, amount_btc, amount_usdt, tran_type, moving_average):
    Orders.create(user_id=user_id, date=date, amount_btc=amount_btc, amount_usdt=amount_usdt, tran_type=tran_type, moving_average=moving_average)
    user = Users.get_or_none(Users.login == 'user')

    if tran_type=='buy':
        now_usd = float(user.balance_usd)-float(amount_usdt)
        now_btc = float(user.balance_btc)+float(amount_btc)
        order_limit_update = Users.update(balance_usd=now_usd, balance_btc=now_btc).where(Users.login == 'user')
        order_limit_update.execute()
    elif tran_type=='sell':
        now_usd = float(user.balance_usd)+float(amount_usdt)
        now_btc = float(user.balance_btc)-float(amount_btc)
        order_limit_update = Users.update(balance_usd=now_usd, balance_btc=now_btc).where(Users.login == 'user')
        order_limit_update.execute()
    return 'created'

def start_thread():
    """
    logging.info('work1 %s' % str(moving_average))

    order = client.create_test_order(
        symbol='BTCUSDT',
        side=Client.SIDE_BUY,
        type=Client.ORDER_TYPE_MARKET,
        quantity=1.100,
    )
    avg_price = client.get_avg_price(symbol='BTCUSDT') """

    klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_5MINUTE, "45 minutes ago UTC")
    end_price = np.array([float(kline[4]) for kline in klines])
    moving_average = np.average(end_price)

    try:
        orders = Orders.select().where(Orders.user_id == 1).limit(5).order_by(Orders.date.desc())
        
        user = Users.get_or_none(Users.login == 'user')
        ma = user.ma
        order_limit = user.order_amount
        if not orders:
            if float(user.balance_usd) > float(order_limit):
                max_amount_btc_buy = float(order_limit)/float(moving_average)
                amount_usdt = float(order_limit)
            elif float(user.balance_usd) != 0:
                max_amount_btc_buy = float(user.balance_usd)/float(moving_average)
                amount_usdt = float(user.balance_usd)

            tran_type = 'buy'
            create_order(1, datetime.datetime.now(), max_amount_btc_buy, amount_usdt, tran_type, moving_average)
        else:
            last_order = orders.get()
            logging.info(last_order.tran_type)
            if last_order.tran_type == 'buy':
                #need to sell when it will be perfect
                if float(moving_average) >= float(last_order.moving_average) + float(user.ma):
                    new_usdt = float(moving_average) * float(last_order.amount_btc)
                    tran_type = 'sell'
                    create_order(1, datetime.datetime.now(), last_order.amount_btc, new_usdt, tran_type, moving_average)
                
            if last_order.tran_type == 'sell':
                #need to buy when it will be perfect
                if float(moving_average) < float(last_order.moving_average) - float(user.ma):
                    if float(user.balance_usd) > float(order_limit):
                        max_amount_btc_buy = float(order_limit)/float(moving_average)
                        amount_usdt = float(order_limit)
                    else:
                        max_amount_btc_buy = float(user.balance_usd)/float(moving_average)
                        amount_usdt = float(user.balance_usd)

                    tran_type = 'buy'
                    create_order(1, datetime.datetime.now(), max_amount_btc_buy, amount_usdt, tran_type, moving_average)
    except Exception as ex:
        logging.info(ex)

    autoThread = threading.Thread()
    autoThread = threading.Timer(60, start_thread, ())
    autoThread.start()
