#!/usr/bin/env python
#
# Poll the Bitfinex order book and print to console.

import os, sys
import multiprocessing
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import configparser

from multiprocessing import Process

from client import Test, Trader

dates, close_data, low_data, high_data, open_data = [], [], [], [], []
dates_mAV, close_data_mAV = [], []

# symbol to query the order book
timeFrame_symbol = ':3h:tBTCUSD'
timeFrame_symbol_mAV = ':12h:tBTCUSD'
symbol = 'tBTCUSD'

# set the parameters to limit the number of bids or asks
parameters = {'limit': 10000, 'sort': -1}

# create the client
#client = bitfinex.Client()
test = Test()

credentials = configparser.ConfigParser()
credentials.read('bfxapi/config/credentials.ini')
API_KEY = credentials['TRADER']['API_KEY']
API_SECRET = credentials['TRADER']['API_SECRET']

trader = Trader(API_KEY, API_SECRET)

# get the order book
#candles = test.candles(timeFrame_symbol, parameters, '/hist')  
#candles_mAV = test.candles(timeFrame_symbol_mAV, parameters, '/hist')

#get the ticker
ticker = test.ticker(symbol)
#print(ticker)
# clear the display, and update values
os.system('clear')

dates, close_data, low_data, high_data, open_data, volume_data = [], [], [], [], [], []

# call historic data & last candle and return combined data
candles = trader.getCandles(timeFrame_symbol, parameters, '/hist')

for candle in candles:
    ts = int(candle[0]) / 1000 
    dates.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
    open_data.append(candle[1])
    close_data.append(candle[2])
    high_data.append(candle[3])
    low_data.append(candle[4])
    volume_data.append(candle[5])

dates = list(reversed(dates))
open_data = list(reversed(open_data))
close_data = list(reversed(close_data))
high_data = list(reversed(high_data))
low_data = list(reversed(low_data))
volume_data = list(reversed(volume_data))

""" for candle_mAV in candles_mAV:
    ts = int(candle_mAV[0]) / 1000
    dates_mAV.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
    close_data_mAV.append(candle_mAV[2])

dates_mAV = list(reversed(dates_mAV))
close_data_mAV = list(reversed(close_data_mAV)) """

#fig = make_subplots(rows=2, cols=1)
fig = go.Figure()
#fig_quick = make_subplots(rows=4, cols=1)
fig_quick = go.Figure()

# create cutout
start = len(close_data)-87 #2920 #87 #9950 #3040 #2920 #8760
end = len(close_data)
#start_mAV = len(close_data_mAV)-730

""" datesCut = dates[start:]
close_dataCut = close_data[start:]
low_dataCut = low_data[start:]
high_dataCut = high_data[start:]
open_dataCut = open_data[start:]

# candles
candle_fig = go.Candlestick(x=datesCut,
                open=open_dataCut, high=high_dataCut,
                low=low_dataCut, close=close_dataCut)
fig_quick.append_trace(candle_fig, row=1, col=1)
fig_quick.update_layout(xaxis_rangeslider_visible=False) """

# rsi
rsi = test.rsi(10, close_data)
stoch_rsi = test.stoch_rsi(10, rsi, 3, 3)

balance_rsi = test.rsi_execute(10, stoch_rsi, close_data, 90, 10, dates, start)
fig_quick.add_trace(go.Scatter(y=balance_rsi[0], x=balance_rsi[1], name='rsi:knowing'))

""" #moving average
averageShort = test.moving_average(close_data, 14) 
averageLong = test.moving_average(close_data, 25)
cross = test.ma_cross(averageShort, averageLong)

balance = test.mAV_execute(cross, close_data, dates, start)
fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name='mAV:knowing'))
#fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name='mAV:knowing'))

#mfi
mfi = test.mfi_execute(close_data, dates, high_data, low_data, volume_data, start, 80, 20)

fig_quick.add_trace(go.Scatter(y=mfi[0], x=mfi[1], name='mfi:balance'))

#combined
rsi = test.rsi(14, close_data)
stoch_rsi = test.stoch_rsi(14, rsi, 3, 3)
# --> this is a method where only buy is possible without limitation of amount != 0
rsi_calculation = test.rsi_execute(8, stoch_rsi, close_data, 100, 5, dates, start)[2]

averageShort = test.moving_average(close_data, 7)
averageLong = test.moving_average(close_data, 22)
mAV_calculation = test.ma_cross(averageShort, averageLong, dates)

balance = test.combined(close_data, dates, rsi_calculation, mAV_calculation, start, len(close_data), low_data, high_data)

fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name='comb:balance:knowing'))

fig_quick.show() """


preMav = []
preStoch_rsi = []
preMfi = []

def preCalcMAV(limit):  
    for x in range(0,1):
        preMav.append(None)

    for period in range(1, limit+1):
        preMav.append(test.moving_average(close_data, period))
    pass

def preCalcRSI(maxPeriod):
    for x in range(0,3):
        preStoch_rsi.append(None)

    for period in range(3, maxPeriod+1):
        rsi = test.rsi(period, close_data)
        preStoch_rsi.append(test.stoch_rsi(period, rsi, 3, 3))
    pass

def preCalcMFI(maxPeriod):
    for x in range(0,3):
        preMfi.append(None)

    for period in range(3, maxPeriod+1):
        preMfi.append(test.calculate_MFI(high_data, low_data, close_data, volume_data, period))
    pass

def worker(low, high):
    highest_Balance = 0
    i_value = 0
    j_value = 0
    
    print("")
    print("")
    print("")
    print("")
    print("")
    print("")

    #moving average
    for i in range(low, high):
        for j in range(1, i):
            averageShort = test.moving_average(close_data, j)
            averageLong = test.moving_average(close_data, i)
            cross = test.ma_cross(averageShort, averageLong)
        
            balance = test.mAV_execute(cross, close_data, dates, start)

            if balance[0][len(balance[0])-1] > highest_Balance:
                highest_Balance = balance[0][len(balance[0])-1]
                i_value = i
                j_value = j

    print(highest_Balance, " i: ", i_value, " j: ", j_value)

def workerMAV(low, high, rsi_calculation, i, lowRsi, highRsi, preMav):
    highest_Balance = 0
    long_value = 0
    short_value = 0
    balance = []

    #moving average
    for longValue in range(low, high):
        averageLong = preMav[longValue]
        for short in range(1, longValue):
            averageShort = preMav[short]
            mAV_calculation = test.ma_cross(averageShort, averageLong, dates)
            
            #logic with combined buy / sell 
            balance = test.combined(close_data, dates, rsi_calculation, mAV_calculation, start, end, low_data, high_data)
            """ print("cur ", balance[0][len(balance[0])-1], " i: ", i, " low: ", lowRsi, " mAVshort ",  short, " mAVlong ", longValue, "                 " , end='      \r')
            sys.stdout.flush() """
            if balance[0][len(balance[0])-1] > highest_Balance:
                highest_Balance = balance[0][len(balance[0])-1]
                long_value = longValue
                short_value = short
                #print("mAV " , highest_Balance, " i: ", i, " low: ", lowRsi, " mAVshort ",  short, " mAVlong ", longValue)

    return highest_Balance, long_value, short_value

def workerRsi(lowRSI, highRSI, lowMAV, highMAV, i, preStoch_rsi, preMav):
    buyOrSellRsi, execute = [[],[]], []
    highest_BalanceMain = 0
    i_value = 0
    low_value, mAV_short = 0, 0
    mAV_long = 0, 0

    stoch_rsi = preStoch_rsi[i]

    for j in range(lowRSI, highRSI+1):
        low = 5
        low = low * j
        low = round(low,1)
        high = 100

        execute = test.buy_or_sell(stoch_rsi, high, low, dates, start, end)

        balance_comb = workerMAV(lowMAV, highMAV, execute, i, low, high, preMav)

        if balance_comb[0] > highest_BalanceMain:
            highest_BalanceMain = balance_comb[0]
            i_value = i
            low_value = low
            mAV_short = balance_comb[2]
            mAV_long = balance_comb[1]
            print("vorläufig: ", highest_BalanceMain, " i: ", i_value, " low: ", low_value, " mAVshort ",  mAV_short, " mAVlong ", mAV_long)

    print("ENDE: ", highest_BalanceMain, " i: ", i_value, " low: ", low_value, " mAVshort ",  mAV_short, " mAVlong ", mAV_long)

""" preCalcMAV(25)
preCalcMFI(9)

workerRsi(1,5,2,25,8, preMfi, preMav) """

""" if __name__ == '__main__':
    jobs = []

    #test mAV
    limit = 45
    preCalcMAV(limit)
    limitP = 18
    preCalcRSI(limitP)
    
    x = 3

    for i in range(multiprocessing.cpu_count()+1):
    #for i in range(multiprocessing.cpu_count()-15):
        if x <=limitP:
            p = multiprocessing.Process(target=workerRsi, args=(1,7,1,limit,x,preStoch_rsi,preMav,))
            x += 1
            jobs.append(p)
            p.start()

    while x <=limitP:
        for job in jobs:
            if not job.is_alive():
                jobs.remove(job)
                p = multiprocessing.Process(target=workerRsi, args=(1,7,1,limit,x,preStoch_rsi,preMav,))
                x += 1
                jobs.append(p)
                print("launching new process")
                p.start() """

#fig_quick.append_trace(go.Scatter(y=balance[0], x=balance[1], name='mAV:knowing'), row=2, col=1)

#simulate rsi and mAV per day
""" solution = test.call_simulation(close_data, dates, close_data_mAV, dates_mAV, start, start_mAV, low_data, high_data)

#fig.append_trace(go.Scatter(y=solution[2], x=solution[3], name='mAV:balance:day'), row=1, col=1)
#fig.append_trace(go.Scatter(y=solution[0], x=solution[1], name='rsi:balance:day'), row=2, col=1)
fig.add_trace(go.Scatter(y=solution[2], x=solution[3], name='mAV:balance:day'))
fig.add_trace(go.Scatter(y=solution[0], x=solution[1], name='rsi:balance:day'))
fig.add_trace(go.Scatter(y=solution[5][0], x=solution[5][1], name='comb:balance:day'))
#fig.append_trace(go.Scatter(y=solution[4][0], x=solution[4][1], name='rsi:day'), row=3, col=1)
fig.show() """


print("")
print("")
print("")
print("")
print("")

low = 5
i = 17
mavLong, mavShort = 23, 9

#av allowing to buy 
av = test.moving_average(close_data, 4)
mav = [[],[]]
for k in range(0, len(av)):
    mav[0].append(av[k])
    mav[1].append(dates[k])

#rsi
rsi = test.rsi(i, close_data)
stoch_rsi = test.stoch_rsi(i, rsi, 3, 3)
rsi_calculation = test.rsi_execute(i, stoch_rsi, close_data, 100, low, dates, start)[2]

#mav
averageShort = test.moving_average(close_data, mavShort)
averageLong = test.moving_average(close_data, mavLong)
mAV_calculation = test.ma_cross(averageShort, averageLong, dates)

#comb
balance = test.combined(close_data, dates, rsi_calculation, mAV_calculation, start, len(close_data), low_data, high_data, mav)
fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name='comb:rsi'+str([low, i, mavShort, mavLong])+ 'average disabled, stoploss5'))

#####
low = 5
i = 17
mavLong, mavShort = 23, 9
mfiLow = 15

#rsi
rsi = test.rsi(i, close_data)
stoch_rsi = test.stoch_rsi(i, rsi, 3, 3)
rsi_calculation = test.rsi_execute(i, stoch_rsi, close_data, 100, low, dates, start)[2]

#mav
averageShort = test.moving_average(close_data, mavShort)
averageLong = test.moving_average(close_data, mavLong)
mAV_calculation = test.ma_cross(averageShort, averageLong, dates)

#mfi
mfi_calculation = test.mfi_execute(close_data, dates, high_data, low_data, volume_data, start, 80, mfiLow)[2]

#combMFI
balance = test.combinedMFI(close_data, dates, rsi_calculation, mAV_calculation, start, len(close_data), low_data, high_data, mfi_calculation, mav)
fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name='comb:rsi+mfi'+str([low, i, mavShort, mavLong, mfiLow])))

fig_quick.show()
#fig.show()
