# -*- coding: utf-8 -*-
"""
Created on Sat Dec 18 18:36:14 2021

@author: Administrator
"""
import mplfinance as mpf
# %%
# 设置mplfinance的蜡烛颜色，up为阳线颜色，down为阴线颜色
my_color = mpf.make_marketcolors(up='r',
                                 down='g',
                                 edge='inherit',
                                 wick='inherit',
                                 volume='inherit')
# 设置图表的背景色
my_style = mpf.make_mpf_style(marketcolors=my_color,
                              figcolor='(0.82, 0.83, 0.85)',
                              gridcolor='(0.82, 0.83, 0.85)')
# %%
import pandas as pd
import numpy as np
'''
# 读取测试数据
data = pd.read_csv('test_data.csv', index_col=0)
# 读取的测试数据索引为字符串类型，需要转化为时间日期类型
data.index = pd.to_datetime(data.index)
mpf.plot(data.iloc[100:200], style=my_style, type='candle', volume=True)
'''
# %%
data3 = pd.read_csv('D:\\Program Files\\Python 3.8.9bit64\\Scripts\\我的量化策略项目'
                    + '\\共享项目文件\\bilibili主站 Pyton项目示例\\用Python写A股量化交易系统'
                    + '\\data资料\\hr600276_test_01.csv', index_col='bob',
                    parse_dates=True)
data4 = pd.DataFrame(data3, columns=['open', 'high', 'low', 'close', 'volume'])
# %%plot(data4,
mpf.plot(data4, style=my_style, type='candle', mav=(2, 5, 10),
         volume=True, show_nontrading=True)
# %%
# data4是测试数据，可以直接下载后读取，在下例中只显示其中100个交易日的数据
plot_data = data4
# 读取显示区间最后一个交易日的数据
last_data = plot_data.iloc[-1]
# 使用mpf.figure()函数可返回一个figure对象，
# 从而进入External axes mode,实现axes和figure对象的自由控制。
fig = mpf.figure(style=my_style, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
# 添加三个图表，四个数字分别代表图表左下角figure中的坐标，图表的宽（0.88),高（0.60)
ax1 = fig.add_axes([0.06, 0.25, 0.88, 0.60])
# 添加第二、三图表时，使用sharex关键字指明与ax1在X轴上对齐，且共用X轴。
ax2 = fig.add_axes([0.06, 0.15, 0.88, 0.10], sharex=ax1)
ax3 = fig.add_axes([0.06, 0.05, 0.88, 0.10], sharex=ax1)
# 设置三张图表的y轴标签
ax1.set_ylabel('price')
ax2.set_ylabel('volume')
ax3.set_ylabel('macd')
# 在figure对象上添加文本对象，用于显示各种价格和标题
fig.text(0.50, 0.94, 'SHSE.600276:')
fig.text(0.12, 0.94, '开/收：')
fig.text(0.14, 0.89, f'{np.round(last_data["open"], 3)} / {np.round(last_data["close"], 3)}')
fig.text(0.14, 0.86, f'{np.round(last_data["close"],12)}')
# %%
# 调用mpf.plot()函数 注意调用的方式跟上一节不同，这里需要指定ax=ax1,volume=ax2,
# 将K线图显示在ax1中,将交易量volume显示在ax2。
mpf.plot(plot_data, ax=ax1, volume=ax2, type='candle', style=my_style)
fig.show()
