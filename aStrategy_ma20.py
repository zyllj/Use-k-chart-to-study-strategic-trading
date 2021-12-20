# -*- coding: utf-8 -*-
# http://hq.sinajs.cn/?format=text&list=sh600519
import requests
from time import sleep
from datetime import datetime, time, timedelta  # timedelta是时间差即：△x或△time
from dateutil import parser  # parser模块功能为将str类型的日期时间对象转变成datetime类型的日时对象
import pandas as pd
import os
import numpy as np  # 利器:ndarry和切片、索引
from gm.api import *

def get_ticks_for_backtesting(tick_path, bar_path):
    """
    # summary:
    # func:get_ticks_for_backtesting, need two params.

    # Parameters
    # -------
    # param1 tick_path: csv file with tick data,
    #     when there is not tick data,used in creating tick data.
    #     tick_path example: 'D: \\python_stock\\stock_data\\600036_ticks.csv'
    # param2 bar_path: csv file with bar data,
    #     used in creating tick data.
    #     bar_path example: 'D: \\python_stock\\stock_data\\600036_5m.csv'

    # Returns
    # -------
    # return: ticks in list with tuples in it, such as
    # [(datetime,last_price),(datetime,last_price)]

    # description:
    # generate tick data, and save it.
    # if we have tick, use it. or else we create tick data by bar data.

    """
    if os.path.exists(tick_path):
        ticks = pd.read_csv(tick_path, parse_dates=['datetime'],
                            index_col='datetime')
        tick_list = []
        for index, row in ticks.iterrows():
            tick_list.append((index, row[0]))
        ticks = np.array(tick_list)
    else:
        bar_5m = pd.read_csv(bar_path)
        ticks = []

        for index, row in bar_5m.iterrows():
            # print(index)
            # print(row)
            # print(str(row['open']) + '-->' + str(row['high']))
            # print(str(row['open']) + '-->' + str(row['low']))
            if row['open'] < 30:
                step = 0.01
            elif row['open'] < 60:
                step = 0.03
            elif row['open'] < 90:
                step = 0.05
            else:
                step = 0.1
            arr = np.arange(row['open'], row['high'], step)
            arr = np.append(arr, row['high'])
            arr = np.append(arr, np.arange(row['open']-step, row['low'], -step))
            arr = np.append(arr, row['low'])
            arr = np.append(arr, row['close'])

            i = 0
            dt = parser.parse(row['datetime']) - timedelta(minutes=5)
            for item in arr:
                ticks.append((dt+timedelta(seconds=0.1*i), item))
                i = 1
        tick_df = pd.DataFrame(ticks, columns=['datetime', 'price'])
        tick_df.to_csv(tick_path, index=0)
    return ticks
# print(get_ticks_for_backtesting.__doc__)

class AstockTrading(object):  # 类class
    # attrabutes
    def _init_(self, strategy_name):
        self._strategy_name = strategy_name
        self._Open = []
        self._High = []
        self._Low = []
        self._Close = []
        self._Dt = []
        self._tick = []
        self._last_bar_start_minute = None
        self._is_new_bar = False
        self._ma20 = None
        self._current_orders = {}
        self._history_orders = {}
        self._order_number = 0
        self._init = False  # for backtesting

    def getTick(self):
        # A股的开盘时间是9.15分，9。15到9。25分之间是集合竟价时间，9。25分成交价是开盘价。
        # 而9。25到9。30分之间不交易，9。30分开始交易。
        page = requests.get('http://hq.sinajs.cn/?format=text&list=sh600519')
        stock_info = page.text
        # stock_info[2]
        # print(stock_info)
        mt_info = stock_info.split(',')
        todayOpen = float(mt_info[1])
        todayDatetime = mt_info[30] + ' ' + mt_info[31]
        trade_todayDatetime = parser.parse(todayDatetime)
        if trade_todayDatetime.time() < time(9, 30):
            trade_todayDatetime = \
                datetime.combine(trade_todayDatetime.date(), time(9, 30))
        self._tick = (trade_todayDatetime, todayOpen)

    def get_history_data_from_local_machine(self):
        self._Open = []
        self._High = []
        self._Low = []
        self._Close = []
        self._Dt = []
        self._tick = []

    def strategy(self):
        # use self._Open,self._High call long or short signals.
        # last < 0.92*ma20,-->buy. (last-ma20)/ma20 < -8%,-->buy.
        # last > 1.08*ma20,-->sell. (last-ma20)/ma20 > 8%,->sell.
        # assume we have history data already,
        # 1、update 5 minutes ma20,not daily data.
        # 2、compare last and ma20,-->buy,sell,pass.
        if self._is_new_bar:  # new bar is created:
            sum_ = 0
            for item in self._Close[1:21]:
                sum_ = sum_+item
            self._ma20 = sum_/20
            if 0 == len(self._current_orders):
                if self._Close[0] < 0.95*self._ma20:
                    volume = int(100000/self._close[0]/100)*100
                    self.buy(self._Close[0]+0.01, volume)
        elif 1 == len(self._current_orders):
            if self._Close[0] > 1.05*self._ma20:  # if I have long position
                key = list(self._current_orders.keys())[0]
                self.sell(key, self._Close[0]-0.01)
        else:  # len() == 2
            raise ValueError('we have more than 1 current orders')
        # long position stop loss?

    def bar_generator_for_backtesting(self, tick):
        # some code to update self._Open,self._High
        if (tick[0].minute % 5 == 0 and
                tick[0].minute != self._last_bar_start_minute):
            # creat new bar
            self._last_bar_stat_minute = tick[0].minute
            self._Open.insert(0, tick[1])
            self._High.insert(0, tick[1])
            self._Low.insert(0, tick[1])
            self._Close.insert(0, tick[1])
            self._Dt.insert(0, tick[1])
            self._is_new_bar = True
        else:
            # upate corrant bar
            self._High[0] = max(self._High[0], tick[1])
            self._Low[0] = min(self._Low[0], tick[1])
            self._Close[0] = tick[1]
            self._Dt[0] = tick[0]
            self._is_new_bar = False

    def run_backtesting(self, ticks):
        """


        Parameters
        ----------
        ticks : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        for tick in ticks:
            self.bar_genarator_for_backtesting(tick)
            if self._init:
                self.strategy()
            else:
                if len(self._open) >= 100:
                    self._init = True
                    self.strategy()

    def buy(self, price, volume):
        """


        Parameters
        ----------
        price : TYPE
            DESCRIPTION.
        volume : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # creat an order
        self._order_number += 1
        key = 'order' + str(self._order_number)
        self._current_orders[key] = {'open_datetim': self._Dt[0], 'open_price':
                                     price, 'volume': volume}

    def sell(self, key, price):
        self._current_orders[key]['close_price'] = price
        self._current_orders[key]['close_datetime'] = self._Dt[0]
        self._current_orders[key]['pnl'] = \
            (price - self._current_orders[key]['open_price']) *\
            self._current_orders[key]['volume'] \
            - price*self._current_orders[key]['volume']*1/1000 \
            - (price + self._current_orders[key]['open_price']) *\
            self._current_orders[key]['volume']*3/10000
        # move order from current orders to history orders
        self._history_orders[key] = self._current_orders.pop(key)

    def runStrategy(self):
        self.getTick()
        self.bar_generator_for_backtesting()
        self.strategy()

if __name__ == '__main__':
    ticks = get_ticks_for_backtesting()

    ast = AstockTrading('ma')
    ast.run_backtesting(ticks)
    ast._current_orders
    ast._history_orders

    profit_orders = 0
    loss_orders = 0
    orders = ast._history_orders
    for key in orders.keys():
        if orders[key]['pnl'] >= 0:
            profit_orders += 1
        else:
            loss_orders += 1

    win_rate = profit_orders/len(orders)
    loss_rate = loss_orders/len(orders)
    # win_rate = 0.75
    # loss_rate = 0.25

    # T = transpose
    orders_df = pd.DataFrame(orders).T
    orders_df.loc[:, 'pnl'].plot.bar()
# %%import mplfinance
import mplfinance as mpf
from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd
# %%
daily = pd.read_csv('https://github.com/matplotlib/mplfinance/blob/master'
                    + '/examples/data/SP500_NOV2019_Hist.csv', index_col=0,
                    parse_dates=True)
daily.index.name = 'Date'
daily.shape
dily.head(3)

# =============================================================================
# astock = AstockTrading()
# astock.get_history_data_from_local_machine()
# while time(9,26) < datatime.now().time() < time(11,32) or \
# 	time(13) < datetime.now().time() < time(15,2):
# 	astock.runStrategy()
# =============================================================================

import pandas as pd
import mplfinance as mpf
import numpy as np  # 利器:ndarry和切片、索引
from gm.api import *
# 可以直接提取数据，掘金终端需要打开，接口取数是通过网络请求的方式，效率一般，行情数据可通过subscribe订阅方式
# 设置token， 查看已有token ID,在用户-密钥管理里获取
set_token('d6d9235bcb79c40daf2c7f8c4b901099fc45d747')
# 查询历史行情, 采用定点复权的方式， adjust指定前复权，adjust_end_time指定复权时间点
data = history(symbol='SHSE.600276', frequency='1d',
               start_time='2021-06-01 09:00:00', end_time='2021-06-30 16:00:00'
               , fields='bob,open,high,low,close,volume'
               , adjust=ADJUST_PREV, adjust_end_time='2021-12-30', df=True)

data.info()
print(data)
data.head(3)['open'][1]
data.tail(2)['close'][1]
data.to_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
            + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
            + '\\data资料\\hr600276_test_01.csv')
data.reindex(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
data1 = pd.DataFrame(data.values, columns=['Date', 'Open', 'High', 'Low',
                                           'Close', 'Volume'])
# %%从.csv读取到dataframe类的对象data2等
data2 = pd.read_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                    + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                    + '\\data资料\\hr600276_test_01.csv')
# %%
data2_1 = pd.read_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                      + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                      + '\\data资料\\hr600276_test_01.csv', index_col=2)
# %%
data3 = pd.read_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                    + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                    + '\\data资料\\hr600276_test_01.csv', index_col='bob',
                    parse_dates=True)
# %%
data4 = pd.DataFrame(data3, columns=['open', 'high', 'low', 'close', 'volume'])
# %%data1.to_csv
data1.to_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
             + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
             + '\\data资料\\hr600276_test_02.csv')
# %%
df = pd.read_table('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                   + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                   + '\\data资料\\hr600276_test_02.csv', sep=',', index_col=['Date'])
# %%
df1 = df[['Open', 'High', 'Low', 'Close', 'Volume']]
# %%
da = []
for x in df1.index:
    da += [parser.parse(x)]
# df1.index = da
# 读取的测试数据df和df1的行row索引index均为字符串类型元素，需转化为日期时间类型。
df1.index = pd.to_datetime(df1.index)
# 设置mplfinance的蜡烛颜色，向上up为阳线颜色，向下down为阴线颜色。
# %%my_style,my_color
my_color = mpf.make_marketcolors(up='r', down='g', edge='inherit',
                                 wick='inherit', volume='inherit')
# 设置图表的背景色
my_style = mpf.make_mpf_style(marketcolors=my_color,
                              figcolor='(0.82, 0.83, 0.85)',
                              gridcolor='(0.82, 0.83, 0.85)')
# %%plot(data4,
mpf.plot(data4, style=my_style, type='candle', mav=(2, 5, 10),
         volume=True, show_nontrading=True)
# %%plot(df1,
mpf.plot(df1.iloc[0:20], style=my_style, type='candle', mav=(2, 5, 10),
         volume=True, show_nontrading=True)
# %%
df1.index.name
pd.to_datetime(df1.index[0])
type(df1.index[0])

mpf.plot(df1)
mpf.plot(df1, type='candle')
mpf.plot(data4, type='candle')
data2 = pd.read_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                    + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                    + '\\data资料\\hr600276_test_01.csv',
                    names=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'],
                    skiprows=1)

fram1 = data.values
fram1.index.name = 'Date'
daily = pd.read_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                    + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                    + '\\data资料\\hr600276_test_01.csv',
                    index_col=0, parse_dates=True)
daily.index.name = 'bob'
mpf.plot(data, type='candle')
mpf.plot(fram1)


ticks = []
for index, row in data.iterrows():
    print(index)
    print(row)
    print(str(row['open']) + '-->' + str(row['high']))
    print(str(row['open']) + '-->' + str(row['low']))

    if row['open'] < 30:
        step = 0.01
    elif row['open'] < 60:
        step = 0.03
    elif row['open'] < 90:
        step = 0.05
    else:
        step = 0.1
    arr = np.arange(row['open'], row['high'], step)
    arr = np.append(arr, row['high'])
    arr = np.append(arr, np.arange(row['open'], row['low'], -step))
    arr = np.append(arr, row['low'])
    arr = np.append(arr, row['close'])
    print(arr)

    for item in arr:
        ticks.append((row['bob'], item))
print(ticks)

# backtestint
# history data
# 5 minute bar -> tick data
# import pandas as pd
# bar_5m = pd.read_csv('D:\\python_stock\\stock_data\\600036_5m.csv')
# bar_5m.head(5)
# bar_5m.tail(5)

# import numpy as np # 利器:ndarry和切片、索引
# np.arange(36.89,37.27,0.01)
# np.arange(36.89-0.01,36.89,0.01)
# np.arange(36.88,36.89,0.01)
# np.arange(36.89-0.01,36.89,-0.01)
# np.arange(36.89-0.01,36.9,0.01)
# np.arange(36.89-0.01,36.91,0.01)
