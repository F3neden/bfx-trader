from re import S
import sys
import asyncio
import json
import pickle
import time
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
sys.path.append('/Users/jan/Documents/Coding/GitHub/bfx-trader/')
sys.path.append('/home/pi/Desktop')
sys.path.append('bfxapi/logic')
from bfxapi import Client
from bfxapi.logic.client import TraderLogic, Backtester
from bfxapi.logic.telegramTraderBot import TelegramBot
import configparser
import numpy as np
import pandas as pd
sys.path.append('../../')

credentials = configparser.ConfigParser()
credentials.read('bfxapi/config/credentials.ini')

API_KEY = credentials['TRADER']['API_KEY']
API_SECRET = credentials['TRADER']['API_SECRET']

telegramBot = TelegramBot()
trader = TraderLogic(API_KEY, API_SECRET, telegramBot)
backtester = Backtester(API_KEY, API_SECRET, telegramBot)
telegramBot.trader = trader

with open('bfxapi/config/config.json', 'r') as f:
  config = json.load(f)

trader.symbol = config['GENERAL']['SYMBOL']
trader.timeframe = config['GENERAL']['TIMEFRAME']

candles = []
dates, close_data, low_data, high_data, open_data, volume_data, ts = [], [], [], [], [], [], []
datesLong, close_dataLong, low_dataLong, high_dataLong, open_dataLong, volume_dataLong, tsLong = [], [], [], [], [], [], []
ash_c, ash_o, ash_h, ash_l, ash_vol, ash_d = [], [], [], [], [], []
preDateLong, preCloseLong, preLowLong, preHighLong, preOpenLong, preVolumeLong = None, 0, 0, 0, 0, 0
preDateShort, preCloseShort, preLowShort, preHighShort, preOpenShort, preVolumeShort = None, 0, 0, 0, 0, 0
candles30m = pd.DataFrame(columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume']) 
candles3h = pd.DataFrame(columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume']) 
ash30m = pd.DataFrame(columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume']) 
ash3h = pd.DataFrame(columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume']) 

counter, former_ts = 0, 0
timestampsLong, timestampsShort = [], []
bfx = Client(
  API_KEY = API_KEY,
  API_SECRET = API_SECRET
  # logLevel= 'DEBUG'
)

# ###### backtester ######
# fig_quick = go.Figure()
# symbols = ['ETHUSD', 'BTCUSD']
# trader.backtest = True
# trader.loggingOn = False
# strategy = config['GENERAL']['ACTIVE_STRATEGY']

# for symbol in symbols:
#   print('Symbol: ', symbol)
#   trader.symbol = symbol

#   backtester = Backtester(API_KEY, API_SECRET, telegramBot)

#   dates, open_data, close_data, high_data, low_data, volume_data, df = backtester.convert_scrapedCandles(startDate="2017-08-01 00:00:00", timeframe=trader.timeframe, symbol=symbol)

#   ash_c, ash_o, ash_h, ash_l, ash_d, ash_vol = [np.nan], [np.nan], [np.nan], [np.nan], [], []
#   ash_d = dates
#   ash_vol = volume_data

#   for x in range(1, len(close_data)):
#       ash_c.append(0.25 * (close_data[x] + open_data[x] + close_data[x] + low_data[x]))
#       ash_o.append(0.5 * (open_data[x-1]+ close_data[x-1]))
#       ash_h.append(max(high_data[x], open_data[x], close_data[x]))
#       ash_l.append(min(low_data[x], open_data[x], close_data[x]))

#   from_to = str(config['BACKTEST'][trader.timeframe]['STRATEGIES'][strategy]['FROM_TO']).split(' TO ')
#   override = {"start": "", "end": ""}
#   override["start"] = "2019-01-01 00:00:00"
#   # override["end"] = "2021-08-23 00:00:00"
#   override["end"] = "max"

#   if override["start"] == "":
#     startDate = dates.index(from_to[0])
#   else: 
#     startDate = dates.index(override["start"])

#   if override["end"] == "":
#     endDate = dates.index(from_to[1])
#   elif override["end"] == "max":
#     endDate = len(dates)-1
#   else:
#     endDate = dates.index(override["end"])

#   lastBuyPrice = 0
#   balance = [[],[], []]
#   writelastBuyPrice = False
#   buyEnabled = True

#   cl = close_data
#   hi = high_data
#   lo = low_data
#   vol = volume_data
#   op = open_data
#   d = dates

#   ash_close = ash_c
#   ash_open = ash_o
#   ash_dates = ash_d

#   balance[0].append(backtester.getAvailBalance())
#   balance[1].append(dates[startDate])
#   balance[2].append("INIT")

#   start = 330
#   for idx in range(startDate,endDate+1):
#     close_data = cl[idx-start:idx+1]
#     dates = d[idx-start:idx+1] 
#     high_data = hi[idx-start:idx+1]
#     low_data = lo[idx-start:idx+1]
#     volume_data = vol[idx-start:idx+1]
#     open_data = op[idx-start:idx+1]

#     ash_c = ash_close[idx-start:idx+1]
#     ash_o = ash_open[idx-start:idx+1]
#     ash_d = ash_dates[idx-start:idx+1]

#     #if idx would exceed list size adjust idx to last element
#     if idx > len(close_data)-1:
#       idx = len(close_data)-1

#     candles3h = pd.DataFrame(list(zip(dates, open_data, high_data, low_data, close_data, volume_data)), 
#                             columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

#     ash3h = pd.DataFrame(list(zip(ash_d, ash_o, ash_c)), 
#                         columns =['Date', 'Open', 'Close'])
    
#     balance, writelastBuyPrice, lastBuyPrice, buyEnabled = trader.buyOrSellCOMBLong(candles3h, ash3h, backtester, balance, writelastBuyPrice, lastBuyPrice)

#   backtester.writeStatistics(balance, op, d, d[start])
#   fig_quick.add_trace(go.Scatter(y=balance[0], x=balance[1], name=symbol+' backtest in trader'))
  
#   # warning if balance does not match
#   if override["end"] == "" and override["start"] == "" and not config['BACKTEST'][trader.timeframe]['STRATEGIES'][strategy]['MAXBALANCE_'+symbol] == balance[0][len(balance[0])-1]: print("!!!!\nBALANCE does not match\n!!!!")

# fig_quick.show()
# sys.exit()

async def log_historical_candles():
  print("start loading hist candles")
  global candles3h, candles30m, ash3h, ash30m
  candles = await bfx.rest.get_public_candles('t'+trader.symbol, 0, None, tf=trader.timeframe, limit='3000')
  for candle in candles:
    candles3h = candles3h.append({'Date': pd.to_datetime(int(candle[0]) / 1000, unit='s'), 'Open': candle[1], 'High': candle[3], 'Low': candle[4], 'Close': candle[2], 'Volume': candle[5]}, ignore_index=True)
    
    if len(candles3h) > 1:
      ash_o = 0.5 * (candles3h['Open'][len(candles3h['Open'])-2] + candles3h['Close'][len(candles3h['Close'])-2])
      ash_c = 0.25 * (candle[2] + candle[1] + candle[2] + candle[4])
      ash_h = (max(candle[3], candle[1], candle[2]))
      ash_l = (min(candle[4], candle[1], candle[2]))
      ash_vol = candle[5]

      ash3h = ash3h.append({'Date': pd.to_datetime(int(candle[0]) / 1000, unit='s'), 'Open': ash_o, 'High': ash_h, 'Low': ash_l, 'Close': ash_c, 'Volume': ash_vol}, ignore_index=True)

  candles3h = candles3h[::-1].reset_index(drop = True)
  print("finished loading hist candles")

async def run():
  await log_historical_candles()

@bfx.ws.on('error')
def log_error(err):
  print ("Error: {}".format(err))

@bfx.ws.on('new_candle')
def log_candle(candle):
  global preDateLong, preCloseLong, preLowLong, preHighLong, preOpenLong, preVolumeLong
  global preDateShort, preCloseShort, preLowShort, preHighShort, preOpenShort, preVolumeShort
  global candles3h, candles30m, ash3h, ash30m
  date = 0

  shared = {"Date":str(datetime.now())}
  fp = open("shared.pkl","wb")
  pickle.dump(shared, fp)
  # print(candle["tf"], " ", candle["mts"], "  -   ", datetime.utcfromtimestamp(int(candle["mts"]) / 1000).strftime('%Y-%m-%d %H:%M:%S'))

  if candle['tf'] == trader.timeframe:
    ts = int(candle["mts"]) / 1000
    date = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    if len(timestampsLong) <= 1:
      timestampsLong.append(ts)

    # write last 4 timestampsLong into array and look if the new ts is already in there
    if not ts in timestampsLong:
        timestampsLong.append(ts)
        if (len(timestampsLong) >= 4):
          del timestampsLong[0]

        candles3h = candles3h.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': candle['open'], 'High': candle['high'], 'Low': candle['low'], 'Close': candle['close'], 'Volume': candle['volume']}, ignore_index=True)

        # adjust last periods data
        candles3h.loc[len(candles3h['Close'])-2,['Close','High','Low','Open','Volume']] = [preCloseLong, preHighLong, preLowLong, preOpenLong, preVolumeLong]
        candles3h.drop(index = candles3h.index[0], inplace=True)

        if len(candles3h) > 1:
          ash_o = 0.5 * (candles3h['Open'][len(candles3h['Open'])-2] + candles3h['Close'][len(candles3h['Close'])-2])
          ash_c = 0.25 * (candle['close'] + candle['open'] + candle['close'] + candle['low'])
          ash_h = (max(candle['high'], candle['open'], candle['close']))
          ash_l = (min(candle['low'], candle['open'], candle['close']))
          ash_vol = candle['volume']

          ash3h = ash3h.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': ash_o, 'High': ash_h, 'Low': ash_l, 'Close': ash_c, 'Volume': ash_vol}, ignore_index=True)
          ash3h.drop(index = ash3h.index[0], inplace=True)

        #check if last buy price has to be set 
        if trader.helper.readFromRuntimeConfig("writelastbuyprice") == 'True':
          #set last buy price
          print("write last buy price's low to file: ", candles3h['Low'][len(candles3h['Low'])-2])
          trader.helper.writeToRuntimeConfig("lastBuyPrice", str(candles3h['Low'][len(candles3h['Low'])-2]))

          #set boolean to false
          trader.helper.writeToRuntimeConfig("writeLastBuyPrice", 'False')

        #excecute trader 
        trader.buyOrSellCOMBLong(candles3h, ash3h, backtester)
    
    preDateLong = date
    preOpenLong = candle['open']
    preCloseLong = candle['close']
    preHighLong = candle['high']
    preLowLong = candle['low']
    preVolumeLong = candle['volume']

  elif candle['tf'] == '30m':
    ts = int(candle["mts"]) / 1000
    date = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    if len(timestampsShort) <= 1:
      timestampsShort.append(ts)

    # write last 4 timestampsShort into array and look if the new ts is already in there
    if not ts in timestampsShort:
        timestampsShort.append(ts)
        if (len(timestampsShort) >= 4):
          del timestampsShort[0]

        candles30m = candles30m.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': candle['open'], 'High': candle['high'], 'Low': candle['low'], 'Close': candle['close'], 'Volume': candle['volume']}, ignore_index=True)

        # adjust last periods data
        candles30m.loc[len(candles30m['Close'])-2,['Close','High','Low','Open','Volume']] = [preCloseShort, preHighShort, preLowShort, preOpenShort, preVolumeShort]
        candles30m.drop(index = candles30m.index[0], inplace=True)

        if len(candles30m) > 1:
          ash_o = 0.5 * (candles30m['Open'][len(candles30m['Open'])-2] + candles30m['Close'][len(candles30m['Close'])-2])
          ash_c = 0.25 * (candle['close'] + candle['open'] + candle['close'] + candle['low'])
          ash_h = (max(candle['high'], candle['open'], candle['close']))
          ash_l = (min(candle['low'], candle['open'], candle['close']))
          ash_vol = candle['volume']

          ash30m = ash30m.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': ash_o, 'High': ash_h, 'Low': ash_l, 'Close': ash_c, 'Volume': ash_vol}, ignore_index=True)
          ash30m.drop(index = ash30m.index[0], inplace=True)

        #check if last buy price has to be set 
        f = open("writeLastBuyPriceMid.txt", "r")
        text = f.read()
        f.close()

        if text == 'True':
          #set last buy price
          print("write last buy price's low to file: ", candles30m['Low'][len(candles30m['Low'])-2])
          f = open("lastBuyPriceMid.txt", "w")
          f.write(str(candles30m['Low'][len(candles30m['Low'])-2]))
          f.close()

          #set boolean to false
          f = open("writeLastBuyPriceMid.txt", "w")
          f.write("False")
          f.close()

        #excecute trader 
        trader.buyOrSellCombShort(candles30m)

    preDateShort = date
    preOpenShort = candle['open']
    preCloseShort = candle['close']
    preHighShort = candle['high']
    preLowShort = candle['low']
    preVolumeShort = candle['volume']

@bfx.ws.on('seed_candle')
def seed_candle(candle):
  global candles3h, candles30m, ash3h, ash30m
  
  if candle['tf'] == trader.timeframe:
    try:
      candles3h['Date'].tolist().index(pd.to_datetime(int(candle['mts']) / 1000, unit='s'))
    except ValueError:
      candles3h = candles3h.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': candle['open'], 'High': candle['high'], 'Low': candle['low'], 'Close': candle['close'], 'Volume': candle['volume']}, ignore_index=True)
    
      if len(candles3h) > 1:
        ash_o = 0.5 * (candles3h['Open'][len(candles3h['Open'])-2] + candles3h['Close'][len(candles3h['Close'])-2])
        ash_c = 0.25 * (candle['close'] + candle['open'] + candle['close'] + candle['low'])
        ash_h = (max(candle['high'], candle['open'], candle['close']))
        ash_l = (min(candle['low'], candle['open'], candle['close']))
        ash_vol = candle['volume']

        ash3h = ash3h.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': ash_o, 'High': ash_h, 'Low': ash_l, 'Close': ash_c, 'Volume': ash_vol}, ignore_index=True)    
    
  elif candle['tf'] == '30m':
    candles30m = candles30m.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': candle['open'], 'High': candle['high'], 'Low': candle['low'], 'Close': candle['close'], 'Volume': candle['volume']}, ignore_index=True)

    if len(candles30m) > 1:
      ash_o = 0.5 * (candles30m['Open'][len(candles30m['Open'])-2] + candles30m['Close'][len(candles30m['Close'])-2])
      ash_c = 0.25 * (candle['close'] + candle['open'] + candle['close'] + candle['low'])
      ash_h = (max(candle['high'], candle['open'], candle['close']))
      ash_l = (min(candle['low'], candle['open'], candle['close']))
      ash_vol = candle['volume']

      ash30m = ash30m.append({'Date': pd.to_datetime(int(candle['mts']) / 1000, unit='s'), 'Open': ash_o, 'High': ash_h, 'Low': ash_l, 'Close': ash_c, 'Volume': ash_vol}, ignore_index=True)

async def start():
  await bfx.ws.subscribe('candles', 't'+trader.symbol, timeframe=trader.timeframe)
  #await bfx.ws.subscribe('candles', 'tBTCUSD', timeframe='30m')

# start loading hist candles
t = asyncio.ensure_future(run())
asyncio.get_event_loop().run_until_complete(t)

# subscribe for new candles
bfx.ws.on('connected', start)
bfx.ws.run()
