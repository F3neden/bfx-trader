from __future__ import absolute_import
import os, sys
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
from tenacity import *
from tenacity.wait import wait_fixed
from bfxapi.logic import telegramTraderBot
from bfxapi.logic.telegramTraderBot import TelegramBot
import configparser
sys.path.append('../../')

import numpy as np
import pandas as pd

PROTOCOL = "https"
HOST = "api.bitfinex.com"
VERSION = "v1"
VERSION2 = "v2"

PATH_SYMBOLS = "symbols"
PATH_TICKER = "ticker/%s"
PATH_TRADES = "trades/%s/hist"
PATH_CANDLES = "candles/trade%s"
PATH_CALC = "auth/calc/order/avail"
PATH_TODAY = "today/%s"
PATH_STATS = "stats/%s"
PATH_LENDBOOK = "lendbook/%s"
PATH_ORDERBOOK = "book/%s"

# HTTP request timeout in seconds
TIMEOUT = 5.0

class Helper:
    def __init__(self, key, secret):
        self.BASE_URL = "https://api.bitfinex.com/"
        #self.URL = "{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION2)
        self.KEY = key
        self.SECRET = secret
        pass
    
    @retry(wait=wait_fixed(15))
    def _get(self, url):
        try:
            return requests.get(url, timeout=TIMEOUT).json()
        except requests.exceptions.Timeout:
            print("timeout error occurred")
            raise TimeoutError
        except requests.exceptions.RequestException as e:
            print("catastrophic error. bail.")
            raise SystemExit(e)
        
    def server(self, version=VERSION):
        return u"{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, version)

    def _build_parameters(self, parameters):
        # sort the keys so we can test easily in Python 3.3 (dicts are not
        # ordered)
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])

    def url_for(self, path, path_arg=None, parameters=None, version=VERSION):

        # build the basic url
        url = "%s/%s" % (self.server(version), path)

        # If there is a path_arg, interpolate it into the URL.
        # In this case the path that was provided will need to have string
        # interpolation characters in it, such as PATH_TICKER
        if path_arg:
            url = url % (path_arg)

        # Append any parameters to the URL.
        if parameters:
            url = "%s?%s" % (url, self._build_parameters(parameters))

        return url

    def _convert_to_floats(self, data):
        """
        Convert all values in a dict to floats
        """
        for key, value in enumerate(data):
            data[key] = float(value)

        return data

    #####################################
    # helper for authenticated requests #
    #####################################

    def _headers(self, path, nonce, body):
        secbytes = self.SECRET.encode(encoding='UTF-8')
        signature = "/api/" + path + nonce + body
        sigbytes = signature.encode(encoding='UTF-8')
        h = hmac.new(secbytes, sigbytes, hashlib.sha384)
        hexstring = h.hexdigest()
        return {
            "bfx-nonce": nonce,
            "bfx-apikey": self.KEY,
            "bfx-signature": hexstring,
            "content-type": "application/json"
        }

    @retry(wait=wait_fixed(15))
    def req(self, path, params = {}, nonce = None):
        try:
            body = params
            rawBody = json.dumps(body)
            if nonce == None:
                nonce = self._nonce()
            headers = self._headers(path, nonce, rawBody)
            url = self.BASE_URL + path
            resp = requests.post(url, headers=headers, data=rawBody, verify=True)
            if resp.text == '["error",10114,"nonce: small"]':
                return Helper.req(self, path, params, str(int(self._nonce())*10))
            else:
                return resp 
        except requests.exceptions.Timeout:
            print("timeout error occurred", resp.text)
            raise TimeoutError
        except Exception as e:
            print("catastrophic error. bail.", resp.text, e)
            raise SystemExit(e)

    def _nonce(self):
        return str(int(round(time.time() * 1000000)))

    def writeToRuntimeConfig(self, option, value, section="runtimeConfig"):
        config = configparser.ConfigParser()
        config.read("bfxapi/config/runtimeConfig.ini")
        config.set(section, option, value)
        with open("bfxapi/config/runtimeConfig.ini", 'w') as configfile:
            config.write(configfile)

    def readFromRuntimeConfig(self, option, section="runtimeConfig"):
        config = configparser.ConfigParser()
        config.read("bfxapi/config/runtimeConfig.ini")
        return config[section][option]

class TraderLogic:
    def __init__(self, key, secret, telegramBot):
        self.helper = Helper(key, secret)
        self.telegramBot = telegramBot
        self.message = ""
        self.symbol = ""
        self.timeframe = ""
        self.buyEnabled = True
        self.backtest = False
        self.loggingOn = True
        with open('bfxapi/config/config.json', 'r') as f:
            self.config = json.load(f)

    def sma(self, data, smaPeriod):
        j = next(i for i, x in enumerate(data) if x is not None)
        our_range = range(len(data))[j + smaPeriod - 1:]
        empty_list = [np.nan] * (j + smaPeriod - 1)
        sub_result = [np.mean(data[i - smaPeriod + 1: i + 1]) for i in our_range]

        return np.array(empty_list + sub_result).tolist()

    def ema(self, values, period):
        values = pd.Series(values)
        return pd.Series.ewm(values, span=period).mean().tolist()
    
    def rma(self, values, period):
        values = pd.Series(values)
        return pd.Series.ewm(values, alpha=1/period).mean().tolist()

    def stoch(self, period, source, high, low):
        stoch_rsi_data = []
        lowest, highest, stoch = 0, 0, 0
        x = 0
        while(source[x] == None):
            x +=1

        for i in range(0, period+x-1):
            stoch_rsi_data.append(None)

        for y in range(x, len(source)-period+1):
            highest = -1
            lowest = 101
            for day in range(y, y+period):
                if high[day] > highest:
                    highest = high[day]
                if low[day] < lowest:
                    lowest = low[day]
            
            if (highest - lowest) == 0:
                stoch_rsi_data.append(np.nan)
            else:
                stoch = 100*((source[day] - lowest) / (highest - lowest))
                stoch_rsi_data.append(stoch)

        return stoch_rsi_data

    def atr(self, df, n=14):
        atr, tr = [[],[]], [[],[]]

        data = df.copy()
        high = data['High']
        low = data['Low']
        close = data['Close']
        data['tr0'] = abs(high - low)
        data['tr1'] = abs(high - close.shift())
        data['tr2'] = abs(low - close.shift())
        tr[0] = data[['tr0', 'tr1', 'tr2']].max(axis=1)
        
        # atr[0] = self.wwma(tr[0], n)
        atr[0] = self.rma(tr[0], n)
        atr[1] = df['Date'].values.tolist()
        return atr

    def calculate_stochRSI(self, open_data, period, smooth, dates):
        rsi = self.calculate_rsi(open_data, period)
        stoch_rsi_data = self.sma(self.sma(self.stoch(period, rsi, rsi, rsi), smooth), smooth)

        with open("data.txt", "w") as myfile:
            myfile.write('='.join(("TIME", str(datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')) + '\n')))
            myfile.write('='.join(("PRICE", str(round(open_data[len(open_data)-1])) + '\n')))
            myfile.write('='.join(("STOCH_RSI", str(round(stoch_rsi_data[len(stoch_rsi_data)-1])) + '\n')))

        self.message = str(datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')) + " - current price " + str(round(open_data[len(open_data)-1])) + " | stoch_rsi " + str(round(stoch_rsi_data[len(stoch_rsi_data)-1],2))  + " "
        
        if self.backtest and self.loggingOn:
            print(dates[len(dates)-1], " - current price ", round(open_data[len(open_data)-1]), " | stoch_rsi ", str(round(stoch_rsi_data[len(stoch_rsi_data)-1])).zfill(2), " ", end="", flush=True)
        elif not self.backtest:
            print(datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), " - current price ", round(open_data[len(open_data)-1]), " | stoch_rsi ", str(round(stoch_rsi_data[len(stoch_rsi_data)-1])).zfill(2), " ", end="", flush=True)
            
        return stoch_rsi_data
    
    def calculate_MFI(self, high_data, low_data, close_data, volume_data, period):
        """
        MFI =  100 - ( 100 / (1+MFRatio))
        MFRatio = (Period PosMoneyFlow)/(Period NegMoneyFlow)
        RawMoneyFlow = TypicalPrice * Volume
        TypicalPrice = (High+Low+Close)/3
        """
        typicalPrice, typicalPriceBefore, MFRatio = [], 0, 0
        MFI = []

        for y in range(0, period-1):
            MFI.append(None)

        #1. calculate typical price
        for x in range(0, len(close_data)):
            typicalPrice.append(self.MFI_typicalPrice(close_data,high_data,low_data,x))

        for x in range(period-1, len(close_data)):
            PosMoneyFlow, NegMoneyFlow = 0, 0
            
            for day in range(x-period+1, x+1):
                higher = True

                try:
                    typicalPriceBefore = typicalPrice[day-1]
                except IndexError:
                    continue
                
                if typicalPriceBefore > typicalPrice[day]:
                    higher =  False

                #2. append raw Money Flow either positive or negative
                if higher:
                    PosMoneyFlow += (typicalPrice[day] * volume_data[day])
                else:
                    NegMoneyFlow += (typicalPrice[day] * volume_data[day])

            #3. calculate RAWMoneyFlow
            if NegMoneyFlow != 0:
                MFRatio = PosMoneyFlow/NegMoneyFlow
            else:
                MFRatio = PosMoneyFlow

            #4. MFI
            MFI.append(round(100- ( 100 / (1 + MFRatio )), 4))

        return MFI
    
    def MFI_typicalPrice(self, close_data, high_data, low_data, day):
        return (high_data[day]+low_data[day]+close_data[day])/3

    def calculate_Resistances(self, close, dates):
        """
        PP = (High + Low + Close) / 3
 		R1 = 2 * PP - Low
 		R2 = PP + (High - Low)
 		R3 = PP + 2 * (High - Low) ----- R3 = High + 2 *  (PP - Low)
        """
        pp, r1, r2, r3, r4 = [[],[]], [[],[]], [[],[]], [[],[]], [[],[]]

        duration = 112

        for i in range(duration*2, len(close)):
            date = dates[i]
            maxV = -sys.maxsize
            minV = sys.maxsize
            for idx in range(i-duration-duration,i+1-duration):
                #max
                if maxV < close[idx]:
                    maxV = close[idx]
                #min
                if minV > close[idx]:
                    minV = close[idx]

            pp[0].append((maxV + minV + close[i]) / 3)
            pp[1].append(dates[i])

            curPP = pp[0][len(pp[0])-1]
            r1[0].append(int(round(2*curPP -minV)))
            r1[1].append(dates[i])

            r2[0].append(int(round(curPP + (maxV-minV))))
            r2[1].append(dates[i])

            r3[0].append(int(round(curPP + 2*(maxV-minV))))
            r3[1].append(dates[i])

            r4[0].append(((close[i-1]/1000 -(close[i-1]/1000)%1)+1)*1000)
            r4[1].append(dates[i])

        return r1, r2, r3, r4

    def calculate_Supports(self, close, dates):
        """
        PP = (High + Low + Close) / 3
 		S1 = 2 * PP - High
 		S2 = PP - (High - Low)
		S3 = PP - 2 * (High - Low)
        """
        pp, s1, s2, s3, s4 = [[],[]], [[],[]], [[],[]], [[],[]], [[],[]]

        duration = 112

        for i in range(duration*2, len(close)):
            date = dates[i]
            maxV = -sys.maxsize
            minV = sys.maxsize
            for idx in range(i-duration-duration,i+1-duration):
                #max
                if maxV < close[idx]:
                    maxV = close[idx]
                #min
                if minV > close[idx]:
                    minV = close[idx]

            pp[0].append((maxV + minV + close[i]) / 3)
            pp[1].append(dates[i+1])

            curPP = pp[0][len(pp[0])-1]
            s1[0].append(int(round(2*curPP - maxV)))
            s1[1].append(dates[i+1])

            s2[0].append(int(round(curPP - (maxV-minV))))
            s2[1].append(dates[i+1])

            s3[0].append(int(round(curPP - 2*(maxV-minV))))
            s3[1].append(dates[i+1])

            s4[0].append(((close[i-1]/1000 -(close[i-1]/1000)%1))*1000)
            s4[1].append(dates[i+1])

        return s1, s2, s3, s4

    def rsi_step_one(self, close_data, period):
        """
        1. calculate for the first 'period' days
            1.1 the average gain 
                if there is a gain, then sum it up and divide it by the number of days with a gain
            1.2 the average loss
                if there is a loss, then sum it up and divide it by the number of days with a loss
            1.3 add 1 to the quotient of the average gain divided by the average loss
            1.4 100 - 100 / '1.3'
        """
        av_gain = 0
        av_loss = 0
        for x in range(0, period):
            relative_change = close_data[x] - close_data[x+1]
            " if negative = gain "
            if relative_change < 0:
                av_gain += abs(relative_change)
            elif relative_change > 0:
                av_loss += abs(relative_change)      

        av_gain = av_gain / period
        av_loss = av_loss / period

        if av_loss == 0:
            rsi = 100
        elif av_gain == 0:
            rsi = 0
        else:
            rsi = 100 - ( 100 / (1 + av_gain/av_loss))

        rsi = round(rsi, 4)
        return rsi, av_gain, av_loss

    def rsi_step_two(self, period, close_data, gain, loss, day):
        """
        2. calculate for every following day
            2.1 add the current gain/loss to the previous average gain/loss which is multiplied with period -1
        """
        relative_change = close_data[day-1] - close_data[day]
        " if negative = gain "
        current_gain, current_loss = 0, 0

        if relative_change < 0:
            current_gain = abs(relative_change)
        elif relative_change > 0:
            current_loss = abs(relative_change)   

        av_gain = (gain*(period-1) + current_gain) / period
        av_loss = (loss*(period-1) + current_loss) / period

        if av_loss == 0:
            rsi = 100
        elif av_gain == 0:
            rsi = 0
        else:
            rsi = 100 - ( 100 / (1 + av_gain / av_loss ))

        rsi = round(rsi, 4)
        return rsi, av_gain, av_loss

    def calculate_rsi(self, close_data, period):
        rsi_data = []

        for x in range(0, period-1):
            rsi_data.append(None)

        step_one = self.rsi_step_one(close_data, period)
        rsi_data.append(step_one[0])
        av_gain = step_one[1]
        av_loss = step_one[2]

        # calculate for all the following days
        for y in range(period, len(close_data)):
            step_two = self.rsi_step_two(period, close_data, av_gain, av_loss, y)
            av_gain = step_two[1]
            av_loss = step_two[2]
            rsi_data.append(step_two[0])

        return rsi_data

    def buyOrSellMAV(self, close_data, dates):
        # load config
        shortValue = self.config['MAV'][self.timeframe][self.symbol]['VALUE_SHORT']
        longValue = self.config['MAV'][self.timeframe][self.symbol]['VALUE_LONG']

        av_short = self.ema(close_data, shortValue)
        av_long = self.ema(close_data, longValue)

        if not self.backtest:
            with open("data.txt", "a") as myfile:
                myfile.write('='.join(("MAV_SHORT", str(round(av_short[len(av_short)-1],0)) + '\n')))
                myfile.write('='.join(("MAV_LONG", str(round(av_long[len(av_long)-1],0)) + '\n')))
        
        if self.loggingOn:
            self.message += " | mav_short " + str(round(av_short[len(av_short)-1],0)) + " mav_long " + str(round(av_long[len(av_long)-1],0))  + " "
            print(" | mav_short ", round(av_short[len(av_short)-1],0), " mav_long ", round(av_long[len(av_long)-1],0)," ", end="", flush=True)

        #if av_short crosses av_long from below to top  = buy
        if av_short[len(av_short)-1] > av_long[len(av_long)-1] and av_short[len(av_short)-2] < av_long[len(av_long)-2]:
            return "buy", dates[len(dates)-1]

        #if av_short falls below av_long = sell
        elif av_short[len(av_short)-1] < av_long[len(av_long)-1] and av_short[len(av_short)-2] > av_long[len(av_long)-2]:
            return "sell", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1]

    def buyOrSellRSI(self, dates, open_data):
        # load config   
        limitLow = self.config['RSI'][self.timeframe][self.symbol]['LIMIT_LOW']
        limitHigh = self.config['RSI'][self.timeframe][self.symbol]['LIMIT_HIGH']
        limitStop = self.config['RSI'][self.timeframe][self.symbol]['LIMIT_STOP']
        period = self.config['RSI'][self.timeframe][self.symbol]['PERIOD']
        smooth = self.config['RSI'][self.timeframe][self.symbol]['SMOOTH']

        rsi_data = self.calculate_stochRSI(open_data, period, smooth, dates)
        
        #overbought = sell
        if rsi_data[len(rsi_data)-1] < limitHigh and rsi_data[len(rsi_data)-2] > limitHigh:
            return "sell", dates[len(dates)-1]

        #oversold = buy
        elif rsi_data[len(rsi_data)-1] > limitLow-limitStop and rsi_data[len(rsi_data)-2] < limitLow:
            return "buy", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1]

    def buyOrSellMFI(self, dates, close_data, high_data, low_data, volume_data):
        # load config   
        limitLow = self.config['MFI'][self.timeframe][self.symbol]['LIMIT_LOW']
        limitHigh = self.config['MFI'][self.timeframe][self.symbol]['LIMIT_HIGH']
        period = self.config['MFI'][self.timeframe][self.symbol]['PERIOD']
        
        MFI = self.calculate_MFI(high_data, low_data, close_data, volume_data, period)
        
        if not self.backtest:
            with open("data.txt", "a") as myfile:
                myfile.write('='.join(("MFI", str(MFI[len(MFI)-1]) + '\n')))

        if self.loggingOn:
            self.message += "| mfi " + str(round(MFI[len(MFI)-1],2)) + '\t'
            print("| mfi ", round(MFI[len(MFI)-1],1) ," ", end="", flush=True)

        #overbought = sell
        if MFI[len(MFI)-1] < limitHigh and MFI[len(MFI)-2] > limitHigh:
            return "sell", dates[len(dates)-1]

        #oversold = buy
        elif MFI[len(MFI)-1] > limitLow and MFI[len(MFI)-2] < limitLow:
            return "buy", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1]

    def buyOrSellResSup(self, ash_c, ash_d, ash_o, open_data):
        resistances = self.calculate_Resistances(ash_o, ash_d)
        supports = self.calculate_Supports(ash_c, ash_d)
        
        if not self.backtest:
            with open("data.txt", "a") as myfile:
                myfile.write('='.join(("RESISTANCE", str(resistances[0][0][len(resistances[0][0])-1]) + '\n')))
                myfile.write('='.join(("SUPPORT", str(supports[0][0][len(supports[0][0])-1]) + '\n')))
        if self.loggingOn:
            # print("resistance ", resistances[0][0][len(resistances[0][0])-1] ," ", end="", flush=True)
            # print("support ", supports[0][0][len(supports[0][0])-1] ," ", end="", flush=True)
            pass

        price = open_data[len(open_data)-1]

        #overbought = buy
        if ( price > resistances[0][0][len(resistances[0][0])-1] 
          or price > resistances[1][0][len(resistances[1][0])-1] 
          or price > resistances[2][0][len(resistances[2][0])-1]
           ):
            return "buy", ash_d[len(ash_d)-1]

        #oversold = sell
        elif (price < supports[0][0][len(supports[0][0])-1] 
          or price < supports[1][0][len(supports[1][0])-1] 
          or price < supports[2][0][len(supports[2][0])-1]
          ):
            return "sell", ash_d[len(ash_d)-1]

        else:
            return None, ash_d[len(ash_d)-1]

    def lowest(self, values, lookback_length):
        """
        helper for buyOrSell trend
        """
        lowest = []
        for i in range(lookback_length-1):
            lowest.append(None)

        for day in range(lookback_length, len(values)+1):
            lowest.append(min(values[day-lookback_length:day]))
        return lowest
    
    def highest(self, values, lookback_length):
        """
        helper for buyOrSell trend
        """
        highest = []
        for i in range(lookback_length-1):
            highest.append(None)

        for day in range(lookback_length, len(values)+1):
            highest.append(max(values[day-lookback_length:day]))
        return highest

    def buyOrSellTrend(self, df):
        # load config
        lookback = self.config['TREND'][self.timeframe][self.symbol]['LOOKBACK']
        smooth = self.config['TREND'][self.timeframe][self.symbol]['SMOOTH']
        atr_length = self.config['TREND'][self.timeframe][self.symbol]['ATR_LENGTH']
        atr_multiplier = self.config['TREND'][self.timeframe][self.symbol]['ATR_MULTIPLIER']

        #initialize
        vola, center, upper, lower, trend = [], [], [], [], []
        atr = self.atr(df, n=atr_length)[0]
        x = 0

        #calculate
        vola = vola + [i * atr_multiplier for i in atr[x:]]
        price = self.sma(df['Close'].values.tolist(), 3)

        l = self.ema(self.lowest(df['Low'].values.tolist(), lookback), smooth)
        h = self.ema(self.highest(df['High'].values.tolist(), lookback), smooth)

        for i in range(x, len(h)):
            center.append((h[i] + l[i]) * 0.5)
            upper.append(center[i] + vola[i])
            lower.append(center[i] - vola[i])

        for j in range(x, len(price)):
            if price[j] > upper[j]: trend.append(1)
            elif price[j] < lower[j]: trend.append(-1)
            else: trend.append(0)

        trend = self.ema(trend, 3)   

        dates = df['Date'].values.tolist()
        k = len(trend)-1
        if not self.backtest:
            with open("data.txt", "a") as myfile:
                myfile.write('='.join(("TREND", str(round(trend[k],1)) + '\n')))

        if self.loggingOn:
            self.message += "| trend " + str(round(trend[k],1)) + " "
            print("| trend ", str(round(trend[k],1)) ," ", end="", flush=True)

        if(trend[k] > 0.0 and trend[k-1] < 0.0):
            return "buy", dates[k], trend[k]
        elif(trend[k] < 0.0 and trend[k-1] > 0.0):
            return "sell", dates[k], trend[k]
        else:
            return None, dates[k], trend[k]

    def cross(self, list1, list2):
        """
        helper method for buyOrSell momentum
        """
        cross = [[],[]]
        cross[0].append("up")
        cross[1].append(list2[0])
        for i in range(1,len(list1)):
            if list1[i-1] < list2[i-1] and list1[i] > list2[i]:
                cross[0].append("up")
                cross[1].append(list2[i])
            elif list1[i-1] > list2[i-1] and list1[i] < list2[i]:
                cross[0].append("down")
                cross[1].append(list2[i])
            else:
                cross[0].append(np.nan)
                cross[1].append(list2[i])
        return cross

    def barssince(self, list, event, currentPos):
        i = currentPos
        while i > 0:
            if list[i] == event:
                break
            i -= 1
        return currentPos-i

    def buyOrSellMomentum(self, close_data, dates):
        # load config   
        rsiLen = self.config['MOMENTUM'][self.timeframe][self.symbol]['LEN_RSI']
        stochLen = self.config['MOMENTUM'][self.timeframe][self.symbol]['LEN_STOCH']
        kSmooth = self.config['MOMENTUM'][self.timeframe][self.symbol]['SMOOTH_K']
        dSmooth = self.config['MOMENTUM'][self.timeframe][self.symbol]['SMOOTH_D']
        limitTop = self.config['MOMENTUM'][self.timeframe][self.symbol]['LIMIT_TOP']
        limitBottom = self.config['MOMENTUM'][self.timeframe][self.symbol]['LIMIT_BOTTOM']
        trendSlowEma = self.config['MOMENTUM'][self.timeframe][self.symbol]['TREND_EMA_SLOW']
        trendFastEma = self.config['MOMENTUM'][self.timeframe][self.symbol]['TREND_EMA_FAST']
        barsDelay = self.config['MOMENTUM'][self.timeframe][self.symbol]['BARS_DELAY']

        # start calculation
        rsi = self.calculate_rsi(close_data, rsiLen)
        k = self.ema(self.stoch(stochLen, rsi, rsi, rsi), kSmooth)
        d = self.ema(k, dSmooth)
        crosses = self.cross(k, d)

        someList = []
        for i in range(len(crosses[0])):
            if crosses[0][i] == "up" and crosses[1][i] <= limitBottom:
                someList.append("golden")
            elif crosses[0][i] == "down" and crosses[1][i] >= limitTop:
                someList.append("death")
            else:
                someList.append(np.nan)

        k = len(someList)-1

        #trend
        emaSlow = self.ema(close_data, trendSlowEma)
        emaFast = self.ema(close_data, trendFastEma)
        uptrend = []
        for j in range(len(emaSlow)):
            if emaFast[j] > emaSlow[j]:
                uptrend.append(True)
            else:
                uptrend.append(False)

        if not self.backtest:
            with open("data.txt", "a") as myfile:
                myfile.write('='.join(("UPTREND", str(uptrend[len(uptrend)-1]) + '\n')))
        
        if self.loggingOn:
            self.message += "| uptrend " + str(uptrend[len(uptrend)-1]) + " "
            print("| uptrend ", str(uptrend[len(uptrend)-1]) ," ", end="", flush=True)
            self.message += "| somelist "+ str(someList[k])+ " | somelist-delay "+ str(someList[k-barsDelay]) + " "
            print("| somelist ", str(someList[k]), " | somelist-delay ", someList[k-barsDelay])

        #buyOrSell
        buyOrSellMomentumOld = [[],[]]
        x = 0
        while x < barsDelay:
            buyOrSellMomentumOld[0].append(np.nan)
            buyOrSellMomentumOld[1].append(dates[x])
            x+=1

        if (uptrend[k] and self.barssince(someList, "death", k) == barsDelay) or (not uptrend[k] and someList[k] == "death"):
            return "sell", dates[len(dates)-1]
        elif someList[k] == "golden" and uptrend[k]:
            return "buy", dates[len(dates)-1]
        else:
            return None, dates[len(dates)-1]

    def buyOrSellCOMBLong(self, candles3h, ash3h, backtester, balance_combined=[[],[],[]], writelastBuyPrice=False, lastBuyPrice=0):
        try:
            buyOrSellRES_SUP, buyOrSellRSI, buyOrSellMAV, buyOrSellMFI, buyOrSellTrend, buyOrSellMomentum = None, None, None, None, None, None

            open_data = candles3h['Open'][:len(candles3h['Open'])].tolist()
            close_data = candles3h['Close'][:len(candles3h['Close'])-1].tolist()
            dates = candles3h['Date'][:len(candles3h['Date'])].tolist()
            high_data = candles3h['High'][:len(candles3h['High'])-1].tolist()
            low_data = candles3h['Low'][:len(candles3h['Low'])-1].tolist()
            volume_data = candles3h['Volume'][:len(candles3h['Volume'])-1].tolist()

            ash_c = ash3h['Close'][:len(ash3h['Close'])-1].tolist()
            ash_d = ash3h['Date'].tolist()
            ash_o = ash3h['Open'].tolist()

            symbol = 't' + self.config['GENERAL']['SYMBOL']
            activeStrategy = self.config['GENERAL']['ACTIVE_STRATEGY']
            
            # calculate strategies
            if (self.backtest and activeStrategy == "RSI;MAV;MFI") or not self.backtest:
                buyOrSellRSI = self.buyOrSellRSI(dates, open_data)
                buyOrSellMFI = self.buyOrSellMFI(dates, close_data, high_data, low_data, volume_data)
                buyOrSellRES_SUP = self.buyOrSellResSup(ash_c, ash_d, ash_o, open_data)

            buyOrSellMAV = self.buyOrSellMAV(close_data, dates)

            if (self.backtest and activeStrategy == "TREND;MOMENTUM") or not self.backtest:
                buyOrSellTrend = self.buyOrSellTrend(candles3h)
                buyOrSellMomentum = self.buyOrSellMomentum(close_data, dates)
            
            # get last buy price
            if not self.backtest:
                #lastBuyPrice = self.requestHistOrders('tBTCUSD')
                textPrice = self.helper.readFromRuntimeConfig("lastBuyPrice")

                if not textPrice == '':
                    lastBuyPrice = float(textPrice)
                else:
                    lastBuyPrice = 0
            elif self.backtest and writelastBuyPrice:
                writelastBuyPrice = False
                lastBuyPrice = low_data[len(low_data)-1]

            if not self.backtest:
                text = self.helper.readFromRuntimeConfig("buyEnabled")
                if text == 'True':
                    self.buyEnabled = True
                else:
                    self.buyEnabled = False

            # enable the possibility to buy
            if buyOrSellMAV[0] == "buy":
                if not self.backtest:
                    self.helper.writeToRuntimeConfig("buyEnabled", 'True')

                    if self.buyEnabled == False:
                        self.telegramBot.sendInfo("Buying is enabled again!")
                self.buyEnabled = True

            if not self.backtest:
                with open("data.txt", "a") as myfile:
                    myfile.write('='.join(("LAST_BUY_PRICE", str(lastBuyPrice) + '\n')))
                    myfile.write('='.join(("BUY_ENABLED", str(self.buyEnabled) + '\n\n')))
                self.telegramBot.sendInfo(self.message)
                balance = self.calcBalance(symbol, 1)[0]
            else:
                balance = backtester.getAvailBalance()
            
            # buy or sell signal 
            reason = self.get_BORS_Signal(activeStrategy, balance, lastBuyPrice, open_data, buyOrSellRES_SUP, buyOrSellRSI, buyOrSellMAV, buyOrSellMFI, buyOrSellTrend, buyOrSellMomentum)

    # buy logic
            if not reason["buy"] == "" and reason["sell"] == "" :

                if not self.backtest:
                    msg = reason["buy"] + " signal == buy"
                    self.telegramBot.sendWarning(msg)
                    print('\n\n' + msg)
                    print("available balance = ", balance)
                    print("utc ", datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), "  buy at ", open_data[len(open_data)-1], " ash high would be: ", high_data[len(high_data)-1], " ash low would be: ", low_data[len(low_data)-1])
                    self.executeBuy(balance, symbol)
                    print("")
                elif self.backtest:
                    backtester.simulate_buy(backtester.calcMaxAmount(open_data[len(open_data)-1]), open_data[len(open_data)-1])
                    writelastBuyPrice = True

                    balance_combined[0].append(backtester.getWalletBalance(open_data[len(open_data)-1]))
                    balance_combined[1].append(dates[len(dates)-1])
                    balance_combined[2].append(reason["buy"])

    # sell logic
            if not reason["sell"] == "" and reason["buy"] == "" :

                if not self.backtest:
                    amount = self.calcBalance(symbol, -1)[0]
                    msg = reason["sell"] + " signal == sell"

                    if amount < -0.00001:
                        if ((lastBuyPrice/open_data[len(open_data)-1])-1) > self.config['GENERAL']['STOPLOSS']:                          
                            #disable the possibility to buy
                            self.helper.writeToRuntimeConfig("buyEnabled", 'False')
                            self.buyEnabled = False

                        self.telegramBot.sendWarning(msg)
                        print('\n\n' + msg)
                        print("amount available to sell = ", amount)
                        print("utc ", datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), "  sell at ", open_data[len(open_data)-1], " ash high would be: ", high_data[len(high_data)-1], " ash low would be: ", low_data[len(low_data)-1])
                        self.executeSell(amount, symbol)
                        print("")
                    else:
                        self.telegramBot.sendInfo("Sell signal ("+ msg +") but not enought available amount! Got " + str(amount) + " but -0.00001 is required.")
                elif self.backtest and backtester.getAvailAmount() > 0.0:
                    backtester.simulate_sell(backtester.getAvailAmount()*100, open_data[len(open_data)-1])
                    lastBuyPrice = 0

                    balance_combined[0].append(backtester.getWalletBalance(open_data[len(open_data)-1]))
                    balance_combined[1].append(dates[len(dates)-1])
                    balance_combined[2].append(reason["sell"])
                    
        except Exception as e:
            print(e)
            self.telegramBot.sendWarning("An error occurred in trader method: " + str(e))

        if self.backtest:
            return balance_combined, writelastBuyPrice, lastBuyPrice, self.buyEnabled    

    def get_BORS_Signal(self, activeStrategy, balance, lastBuyPrice, open_data, buyOrSellRES_SUP=None, buyOrSellRSI=None, buyOrSellMAV=None, buyOrSellMFI=None, buyOrSellTrend=None, buyOrSellMomentum=None):
        reason = {"buy": "", "sell": ""}

        ## buy logic ##
        if activeStrategy == "RSI;MAV;MFI" and balance > 20.0:
            if self.buyEnabled and not buyOrSellRES_SUP[0] == "sell" and buyOrSellRSI[0] == "buy" :
                reason["buy"] = "RSI"
            elif buyOrSellRES_SUP[0] == "buy":
                reason["buy"] = "RESISTANCE"

        elif activeStrategy == "TREND;MOMENTUM" and balance > 20.0:
            if buyOrSellTrend[0] == "buy":
                reason["buy"] = "TREND"
            elif buyOrSellMomentum[0] == "buy":
                reason["buy"] = "MOMENTUM"

        ## sell logic ##
        if activeStrategy == "RSI;MAV;MFI":
            if buyOrSellMAV[0] == "sell": 
                reason["sell"] =  "MAV"
            elif buyOrSellMFI[0] == "sell":
                reason["sell"] = "MFI"
            elif buyOrSellRES_SUP[0] == "sell":
                reason["sell"] = "SUPPORT"
            elif ((lastBuyPrice/open_data[len(open_data)-1])-1) > self.config['GENERAL']['STOPLOSS']:
                reason["sell"] = "STOPLOSS"
                self.buyEnabled = False

        elif activeStrategy == "TREND;MOMENTUM":
            if buyOrSellTrend[0] == "sell":
                reason["sell"] = "TREND"
            elif buyOrSellMomentum[0] == "sell":
                reason["sell"] = "MOMENTUM"

        return reason

    def buyOrSellCombShort(self, candles30m):
        print("hi")

    def calcBalance(self, symbol, buy_or_sell):
        """
        buy_or_sell 
        1 == buy 
        -1 == sell
        """
        endpoint = "v2/auth/calc/order/avail"
        payload = {
            "symbol": symbol,
            "dir": buy_or_sell,
            "rate": '1',
            "type": 'EXCHANGE'
        }
        r = self.helper.req(endpoint, payload)
        json_resp = r.json()

        try:
            json_resp[0]
        except:
            return json_resp

        return json_resp

    def getTicker(self, symbol):
        return self.helper._get(self.helper.url_for(PATH_TICKER, (symbol), version=VERSION2))

    def getCandles(self, timeFrame_symbol, parameters, section):
        return self.helper._get(self.helper.url_for(PATH_CANDLES+section, (timeFrame_symbol), parameters=parameters, version=VERSION2))

    def requestHistTrades(self, symbol="", start=""):
        try:
            payload = {
                "limit": 2500,
                "start": start
            }
            
            if not symbol == "":
                symbol += "/"
            response = self.helper.req("v2/auth/r/trades/" + symbol + "hist", payload)

            if response.status_code == 200:
                return response.json()

            else:
                raise Exception('error while requesting hist trades, status_code = ', response.status_code, response.text)
        except Exception as e:
            self.telegramBot.sendWarning(e)
            return ''

    def requestHistOrders(self, symbol):
        try:
            payload = {
                "limit": 2500
            }

            response = self.helper.req("v2/auth/r/orders/" + symbol + "/hist", payload)
            # loop over items
            # check 07 for a positive amount -> only last BUY price wanted
            # check 17 for price
            if response.status_code == 200:
                return response.json()

                # #getLastBuyPrice
                # for trade in r:
                #     if trade[7] > 0:
                #         return float(trade[17])
            else:
                raise Exception('error while requesting hist orders, status_code = ', response.status_code, response.text)
        except Exception as e:
            self.telegramBot.sendWarning(e)
            return ''

    def requestBalances(self):
        """
        Fetch balances

        :return:
        """
        response = self.helper.req("v2/auth/r/wallets")
        if response.status_code == 200:
          return response.json()
        else:
          print('error while requesting Balance, status_code = ', response.status_code)
          return ''

    def request_active_orders(self):
        # Fetch active orders
        response = self.req("v2/auth/r/orders")
        if response.status_code == 200:
          return response.json()
        else:
          print('error, status_code = ', response.status_code)
          return ''
    
    def executeBuy(self, balance, symbol): 
        price = self.getTicker(symbol)

        if balance >= 25.0:
            amount = balance / price[6]
            print("try to buy an amount of ", amount, " at a price of ", price[6])

            try:
                order_response = self.submit_order(symbol, price[6], amount)

                if order_response[0] == 'error':
                    if order_response[1] == 10001:
                        print(order_response[2])
                        TraderLogic.executeBuy(self, balance-0.1)
                    else:
                        print("uncaught error")
                        print(order_response[3])
                elif order_response[6] == 'SUCCESS':
                    self.telegramBot.sendWarning("Successfully bought " + str(balance) + " at " + str(price) + "!")
                    order_id = order_response[4][0][2]
                    status = order_response[4][0][13]
                    print("Order : ", order_id, " with status: ", status)

                    self.helper.writeToRuntimeConfig("writeLastBuyPrice", 'True')
                    # f = open("writeLastBuyPrice.txt", "w")
                    # f.write("True")
                    # f.close()
            except:
                print(order_response[2])
                self.telegramBot.sendWarning("An exception occurred while trying to buy. Trying again!\n" + str(order_response[2]))
                TraderLogic.executeBuy(self, balance-0.1)

    def executeSell(self, amount, symbol):
        price = self.getTicker(symbol)
        print("last price ", price[6])

        try:
            order_response = self.submit_order(symbol, price[6], amount)

            if order_response[0] == 'error':
                print("uncaught error")
                print(order_response[2])
                TraderLogic.executeSell(self, amount+0.00001)

            elif order_response[6] == 'SUCCESS':
                self.telegramBot.sendWarning("Successfully sold " + str(amount) + " at " + str(price) + "!")
                order_id = order_response[4][0][2]
                status = order_response[4][0][13]
                print("Order : ", order_id, " with status: ", status)

                #reset last buy price
                self.helper.writeToRuntimeConfig("lastBuyPrice", str(0))
                # f = open("lastBuyPrice.txt", "w")
                # f.write(str(0))
                # f.close()
        except:
            print("uncaught error in try")
            print(order_response[2])
            self.telegramBot.sendWarning("An exception occurred while trying to sell. Trying again!\n" + str(order_response[2]))
            TraderLogic.executeSell(self, amount+0.00001)

    def submit_order(self, symbol, price, amount, market_type='EXCHANGE LIMIT',
                           hidden=False, price_trailing=None, price_aux_limit=None,
                           oco_stop_price=None, close=False, reduce_only=False,
                           post_only=False, oco=False, aff_code=None, time_in_force=None,
                           leverage=None, gid=None):
        """
        Submit a new order

        # Attributes
        @param gid: assign the order to a group identifier
        @param symbol: the name of the symbol i.e 'tBTCUSD
        @param price: the price you want to buy/sell at (must be positive)
        @param amount: order size: how much you want to buy/sell,
          a negative amount indicates a sell order and positive a buy order
        @param market_type	Order.Type: please see Order.Type enum
          amount	decimal string	Positive for buy, Negative for sell
        @param hidden: if True, order should be hidden from orderbooks
        @param price_trailing:	decimal trailing price
        @param price_aux_limit:	decimal	auxiliary Limit price (only for STOP LIMIT)
        @param oco_stop_price: set the oco stop price (requires oco = True)
        @param close: if True, close position if position present
        @param reduce_only: if True, ensures that the executed order does not flip the opened position
        @param post_only: if True, ensures the limit order will be added to the order book and not
          match with a pre-existing order
        @param oco: cancels other order option allows you to place a pair of orders stipulating
          that if one order is executed fully or partially, then the other is automatically canceled
        @param aff_code: bitfinex affiliate code
        @param time_in_force:	datetime for automatic order cancellation ie. 2020-01-01 10:45:23
        @param leverage: the amount of leverage to apply to the order as an integer
        """
        payload = {
            "type": str(market_type),
            "symbol": symbol,
            "amount": str(amount),
            "price": str(price),
            "meta": {}
        }
        # calculate and add flags
        flags = 0
        #flags = calculate_order_flags(hidden, close, reduce_only, post_only, oco)
        payload['flags'] = flags
        # add extra parameters
        if price_trailing != None:
            payload['price_trailing'] = price_trailing
        if price_aux_limit != None:
            payload['price_aux_limit'] = price_aux_limit
        if oco_stop_price != None:
            payload['price_oco_stop'] = str(oco_stop_price)
        if time_in_force != None:
            payload['tif'] = time_in_force
        if gid != None:
            payload['gid'] = gid
        if leverage != None:
            payload['lev'] = str(leverage)
        if aff_code != None:
            payload['meta']['aff_code'] = str(aff_code)
        endpoint = "v2/auth/w/order/submit"

        #signed_payload = self._sign_payload(payload)
        #r = requests.post(self.URL + "/order/new", headers=signed_payload, verify=True)
        r = self.helper.req(endpoint, payload)
        json_resp = r.json()

        try:
            json_resp[0]
        except:
            return json_resp

        return json_resp


        """ raw_notification = await self.post(endpoint, payload)
        return Notification.from_raw_notification(raw_notification) """

class Backtester:
    def __init__(self, key, secret, bot):
        self.trader = TraderLogic(key, secret, bot)
        self.balance = 100
        self.amount = 0

    def simulate_buy(self, amount, price):
        if(self.getAvailBalance() > 0 and self.getAvailBalance() >= (amount * price / 0.9985)):
            self.setAvailBalance(round(self.getAvailBalance() - (amount * price / 0.9985),5))
            self.setAvailAmount(self.getAvailAmount() + amount)
        else:
            self.setAvailAmount(self.getAvailAmount() + self.calcMaxAmount(price))
            self.setAvailBalance(0.0)

    def simulate_sell(self, amount, price):
        if(self.getAvailAmount() > 0 and amount <= self.getAvailAmount()):
            self.setAvailBalance(self.getAvailBalance() + amount * price)
            self.setAvailAmount(self.getAvailAmount() - amount)
        else:
            self.setAvailBalance(self.getAvailBalance() + self.getAvailAmount() * price)
            self.setAvailAmount(0.0)

    def calcMaxAmount(self, price):
        return round(((0.9985 * self.getAvailBalance()) / price), 6)
    
    def getWalletBalance(self, price):
        return round(self.getAvailBalance() + self.getAvailAmount() * price,5)

    def getAvailAmount(self):
        return self.amount

    def setAvailAmount(self, amount):
        self.amount = amount

    def getAvailBalance(self):
        return self.balance

    def setAvailBalance(self, balance):
        self.balance = balance

    def convert_scrapedCandles(self, startDate=None, timeframe="", symbol=""):
        dates, close_data, low_data, high_data, open_data, volume_data = [], [], [], [], [], []

        # open the file in read binary mode
        if timeframe == "":
            file = open("candles1h_2017:09:01ETHUSD", "rb")
        else:
            #get matching file
            for file in os.listdir('candles/'):
                if file.endswith(symbol) and file.startswith('candles'+timeframe):
                    fileName = file
                    break

            file = open('candles/'+fileName, "rb")

        #read the file to numpy array
        candles = np.load(file)

        for candle in candles:
            ts = int(candle[0]) / 1000 
            dates.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
            open_data.append(candle[1])
            high_data.append(candle[3])
            low_data.append(candle[4])
            close_data.append(candle[2])
            volume_data.append(abs(candle[5]))

        if not startDate == None:
            cutIdx = dates.index(startDate)
            dates = dates[:cutIdx+1]
            open_data = open_data[:cutIdx+1]
            high_data = high_data[:cutIdx+1]
            low_data = low_data[:cutIdx+1]
            close_data = close_data[:cutIdx+1]
            volume_data = volume_data[:cutIdx+1]

        df = pd.DataFrame(list(zip(dates, open_data, high_data, low_data, close_data)), 
            columns =['Date', 'Open', 'High', 'Low', 'Close']) 
        df = df.iloc[::-1]

        dates = list(reversed(dates))
        open_data = list(reversed(open_data))
        close_data = list(reversed(close_data))
        high_data = list(reversed(high_data))
        low_data = list(reversed(low_data))
        volume_data = list(reversed(volume_data))

        return dates, open_data, close_data, high_data, low_data, volume_data, df

    def writeStatistics(self, balance_combined, open_data, dates, start):
        print("")
        print("")
        print("")
        listOfTrades = pd.DataFrame(columns =['Date', 'Reason', 'Signal', 'Price', 'Profit', 'Balance']) 
        for i in range(1,len(balance_combined[0])):
            try:
                price = open_data[dates.index(balance_combined[1][i])]
            except ValueError:
                print("could not find ", dates.index(balance_combined[1][i]))

            if i%2 == 0:
                signal = "sell"
                balance = balance_combined[0][i]
                profit = balance - balance_combined[0][i-1] 
                profit = (profit/balance_combined[0][i-1])*100
                listOfTrades = listOfTrades.append({'Date': balance_combined[1][i], 'Reason': balance_combined[2][i], 'Signal': signal, 'Price': price, 'Profit': profit, 'Balance': balance}, ignore_index=True)
            else:
                if not i+1 >= len(balance_combined[0]):
                    signal = "buy"
                    balance = balance_combined[0][i+1]
                    profit = balance - balance_combined[0][i]
                    profit = (profit/balance_combined[0][i])*100
                    listOfTrades = listOfTrades.append({'Date': balance_combined[1][i], 'Reason': balance_combined[2][i], 'Signal': signal, 'Price': price}, ignore_index=True)
        trades = ((len(listOfTrades))/2)

        print(listOfTrades.to_string())
        # print(listOfTrades.loc[listOfTrades['Reason'] == 'RESISTANCE'])
        # print(listOfTrades.loc[listOfTrades['Profit'] < 0])
        print("Profitable trades: ", round((sum(n > 0 for n in listOfTrades['Profit']) / trades) * 100,1), "%")
        print("Average return per trade: ", round(listOfTrades['Profit'].sum(axis=0)/trades,2), "%")
        print("Max gain in a trade: ", round(listOfTrades['Profit'].max(),2), "%")
        print("Max drawdown in a trade: ", round(listOfTrades['Profit'].min(),2), "%")
        print("Buy and hold balance: ",((100 - 0.002*100) / open_data[dates.index(start)]) * open_data[len(open_data)-1])