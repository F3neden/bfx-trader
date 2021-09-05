import os
import sys
import asyncio
import time
import configparser
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
sys.path.append('/Users/jan/Documents/Coding/bitfinex-api-py/')
sys.path.append('../../../')
from bfxapi import Client
import bfxapi.logic.client  
from bfxapi.logic.client import Trader, Backtester

credentials = configparser.ConfigParser()
credentials.read('bfxapi/config/credentials.ini')
API_KEY = credentials.TRADER['API_KEY']
API_SECRET = credentials.TRADER['API_SECRET']

trader = Trader(API_KEY, API_SECRET)


candles = []
dates, close_data, low_data, high_data, open_data, volume_data = [], [], [], [], [], []
ash_c, ash_o, ash_h, ash_l, ash_vol, ash_d = [], [], [], [], [], []

counter, former_ts = 0, 0
timestamps = []
bfx = Client(
  API_KEY = API_KEY,
  API_SECRET = API_SECRET
  # logLevel= 'DEBUG'
)

""" fig_quick = go.Figure()

# set the parameters to limit the number of bids or asks
timeFrame_symbol = ':3h:tBTCUSD'
parameters = {'limit': 10000, 'sort': -1}
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

ash_d = dates[1:]
ash_vol = volume_data[1:]

for x in range(1, len(close_data)):
    ash_c.append(0.25 * (close_data[x] + open_data[x] + close_data[x] + low_data[x]))
    ash_o.append(0.5 * (open_data[x-1]+ close_data[x-1]))
    ash_h.append(max(high_data[x], open_data[x], close_data[x]))
    ash_l.append(min(low_data[x], open_data[x], close_data[x]))

backtester = Backtester(API_KEY, API_SECRET)
balance = backtester.buyOrSellTest(close_data,high_data,low_data,volume_data,dates,4,86,5,95,14,3,0.042,open_data, ash_c, ash_o, ash_d)

fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name='comb:rsi+mfi+ash+resistance'+str([5, 17, 9, 23, 90])+ 'close stoploss42'))
fig_quick.show()
sys.exit() """

async def log_historical_candles():
  dates, close_data, low_data, high_data, open_data, volume_data = [], [], [], [], [], []

  global candles 
  candles = await bfx.rest.get_public_candles('tBTCUSD', 0, None, tf='3h', limit='10000')
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
  candles = list(reversed(candles))

  print (candles[len(candles)-1])

async def run():
    await log_historical_candles()

@bfx.ws.on('error')
def log_error(err):
  print ("Error: {}".format(err))

@bfx.ws.on('new_candle')
def log_candle(candle):
  global preDate, preClose, preLow, preHigh, preOpen, preVolume
  date = 0
  newCandle = False

  # print(candle["tf"], " ", candle["mts"], "  -   ", datetime.utcfromtimestamp(int(candle["mts"]) / 1000).strftime('%Y-%m-%d %H:%M:%S'))

  ts = int(candle["mts"]) / 1000
  date = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

  if len(timestamps) <= 1:
    timestamps.append(ts)

  # write last 4 timestamps into array and look if the new ts is already in there
  if not ts in timestamps:
      timestamps.append(ts)
      if (len(timestamps) >= 4):
        del timestamps[0]
      dates.append(date)
      open_data.append(candle['open'])
      close_data.append(candle['close'])
      high_data.append(candle['high'])
      low_data.append(candle['low'])
      volume_data.append(candle['volume'])

      # adjust last periods data 
      close_data[len(close_data)-2] = preClose
      high_data[len(high_data)-2] = preHigh
      low_data[len(low_data)-2] = preLow
      open_data[len(low_data)-2] = preOpen
      volume_data[len(volume_data)-2] = preVolume

      if len(dates) > 1:
        ash_o.append(0.5 * (open_data[len(open_data)-2] + close_data[len(close_data)-2]))
        ash_c.append(0.25 * (candle['close'] + candle['open'] + candle['close'] + candle['low']))
        ash_h.append(max(candle['high'], candle['open'], candle['close']))
        ash_l.append(min(candle['low'], candle['open'], candle['close']))
        ash_vol.append(candle['volume'])
        ash_d.append(date)

        ash_o.pop(0)
        ash_c.pop(0)
        ash_l.pop(0)
        ash_h.pop(0)
        ash_vol.pop(0)
        ash_d.pop(0)

      dates.pop(0)
      open_data.pop(0)
      close_data.pop(0)
      high_data.pop(0)
      low_data.pop(0)
      volume_data.pop(0)

      #check if last buy price has to be set 
      f = open("writeLastBuyPrice.txt", "r")
      text = f.read()
      f.close()
      if text == 'True':

        #set last buy price
        print("write last buy price's low to file: ", low_data[len(low_data)-2])
        f = open("lastBuyPrice.txt", "w")
        f.write(str(low_data[len(low_data)-2]))
        f.close()

        #set boolean to false
        f = open("writeLastBuyPrice.txt", "w")
        f.write("False")
        f.close()

      #excecute trader 
      trader.buyOrSellCOMB(open_data, high_data, low_data, close_data, volume_data, dates, 4, 86, 5, 95, 14, 3, 0, 0.042, close_data, ash_c, ash_o, ash_d)
  
  preDate = date
  preOpen = candle['open']
  preClose = candle['close']
  preHigh = candle['high']
  preLow = candle['low']
  preVolume = candle['volume']

@bfx.ws.on('seed_candle')
def seed_candle(candle):
  global dates, close_data, low_data, high_data, open_data, volume_data

  ts = int(candle['mts']) / 1000 
  dates.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
  open_data.append(candle['open'])
  close_data.append(candle['close'])
  high_data.append(candle['high'])
  low_data.append(candle['low'])
  volume_data.append(candle['volume'])

  if len(dates) > 1:
    ash_o.append(0.5 * (open_data[len(open_data)-2] + close_data[len(close_data)-2]))
    ash_c.append(0.25 * (candle['close'] + candle['open'] + candle['close'] + candle['low']))
    ash_h.append(max(candle['high'], candle['open'], candle['close']))
    ash_l.append(min(candle['low'], candle['open'], candle['close']))
    ash_vol.append(candle['volume'])
    ash_d.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))

async def start():
  await bfx.ws.subscribe('candles', 'tBTCUSD', timeframe='3h')

bfx.ws.on('connected', start)
bfx.ws.run()