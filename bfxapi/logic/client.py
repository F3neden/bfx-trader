from __future__ import absolute_import
import os
import requests
import json
import base64
import hmac
import hashlib
import time
from datetime import datetime
import pytz
from tenacity import *

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



class TradeClient:
    """
    Authenticated client for trading through Bitfinex API
    """

    def __init__(self, key, secret):
        self.URL = "{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)
        self.KEY = key
        self.SECRET = secret
        pass

    @property
    def _nonce(self):
        """
        Returns a nonce
        Used in authentication
        """
        return str(time.time() * 1000000)

    def _sign_payload(self, payload):
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf8'))

        h = hmac.new(self.SECRET.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()
        return {
            "X-BFX-APIKEY": self.KEY,
            "X-BFX-SIGNATURE": signature,
            "X-BFX-PAYLOAD": data
        }

    def place_order(self, amount, price, side, ord_type, symbol='btcusd', exchange='bitfinex'):
        """
        Submit a new order.
        :param amount:
        :param price:
        :param side:
        :param ord_type:
        :param symbol:
        :param exchange:
        :return:
        """
        payload = {

            "request": "/v1/order/new",
            "nonce": self._nonce,
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "exchange": exchange,
            "side": side,
            "type": ord_type

        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/new", headers=signed_payload, verify=True)
        json_resp = r.json()

        try:
            json_resp['order_id']
        except:
            return json_resp['message']

        return json_resp

    def delete_order(self, order_id):
        """
        Cancel an order.
        :param order_id:
        :return:
        """
        payload = {
            "request": "/v1/order/cancel",
            "nonce": self._nonce,
            "order_id": order_id
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel", headers=signed_payload, verify=True)
        json_resp = r.json()

        try:
            json_resp['avg_execution_price']
        except:
            return json_resp['message']

        return json_resp

    def delete_all_orders(self):
        """
        Cancel all orders.

        :return:
        """
        payload = {
            "request": "/v1/order/cancel/all",
            "nonce": self._nonce,
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel/all", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def status_order(self, order_id):
        """
        Get the status of an order. Is it active? Was it cancelled? To what extent has it been executed? etc.
        :param order_id:
        :return:
        """
        payload = {
            "request": "/v1/order/status",
            "nonce": self._nonce,
            "order_id": order_id
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/status", headers=signed_payload, verify=True)
        json_resp = r.json()

        try:
            json_resp['avg_execution_price']
        except:
            return json_resp['message']

        return json_resp

    def active_orders(self):
        """
        Fetch active orders
        """

        payload = {
            "request": "/v1/orders",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/orders", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def active_positions(self):
        """
        Fetch active Positions
        """

        payload = {
            "request": "/v1/positions",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/positions", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def claim_position(self, position_id):
        """
        Claim a position.
        :param position_id:
        :return:
        """
        payload = {
            "request": "/v1/position/claim",
            "nonce": self._nonce,
            "position_id": position_id
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/position/claim", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def past_trades(self, timestamp=0, symbol='btcusd'):
        """
        Fetch past trades
        :param timestamp:
        :param symbol:
        :return:
        """
        payload = {
            "request": "/v1/mytrades",
            "nonce": self._nonce,
            "symbol": symbol,
            "timestamp": timestamp
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/mytrades", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def place_offer(self, currency, amount, rate, period, direction):
        """

        :param currency:
        :param amount:
        :param rate:
        :param period:
        :param direction:
        :return:
        """
        payload = {
            "request": "/v1/offer/new",
            "nonce": self._nonce,
            "currency": currency,
            "amount": amount,
            "rate": rate,
            "period": period,
            "direction": direction
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offer/new", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def cancel_offer(self, offer_id):
        """

        :param offer_id:
        :return:
        """
        payload = {
            "request": "/v1/offer/cancel",
            "nonce": self._nonce,
            "offer_id": offer_id
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offer/cancel", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def status_offer(self, offer_id):
        """

        :param offer_id:
        :return:
        """
        payload = {
            "request": "/v1/offer/status",
            "nonce": self._nonce,
            "offer_id": offer_id
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offer/status", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def active_offers(self):
        """
        Fetch active_offers
        :return:
        """
        payload = {
            "request": "/v1/offers",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offers", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def balances(self):
        """
        Fetch balances

        :return:
        """
        payload = {
            "request": "/v1/balances",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/balances", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

    def history(self, currency, since=0, until=9999999999, limit=500, wallet='exchange'):
        """
        View you balance ledger entries
        :param currency: currency to look for
        :param since: Optional. Return only the history after this timestamp.
        :param until: Optional. Return only the history before this timestamp.
        :param limit: Optional. Limit the number of entries to return. Default is 500.
        :param wallet: Optional. Return only entries that took place in this wallet. Accepted inputs are: “trading”,
        “exchange”, “deposit”.
        """
        payload = {
            "request": "/v1/history",
            "nonce": self._nonce,
            "currency": currency,
            "since": since,
            "until": until,
            "limit": limit,
            "wallet": wallet
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/history", headers=signed_payload, verify=True)
        json_resp = r.json()

        return json_resp

class Test:
    def __init__(self):
        self.client = Client()
        #self.balance = 100
        pass

    def ticker(self, symbol):
        """
        GET /ticker/:symbol
        curl https://api-pub.bitfinex.com/v2/ticker/tBTCUSD
        curl https://api.bitfinex.com/v1/ticker/btcusd
        {
            'ask': '562.9999',
            'timestamp': '1395552290.70933607',
            'bid': '562.25',
            'last_price': u'562.25',
            'mid': u'562.62495'}
        """
        data = self.client._get(self.client.url_for(PATH_TICKER, (symbol), version=VERSION2))
        #data = self._get(self.url_for(PATH_TICKER, (symbol)))

        # convert all values to floats
        return self.client._convert_to_floats(data)

    def calc_balance(self, price, amount):
        self.balance = price * amount 
        return self.balance

    def candles(self, timeFrame_symbol, parameters, section):
        """
        https://api-pub.bitfinex.com/v2/candles/trade:TimeFrame:Symbol/Section
        """

        return self.client._get(self.client.url_for(PATH_CANDLES + section, (timeFrame_symbol), parameters=parameters, version=VERSION2))

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

        return rsi, av_gain, av_loss

    def rsi(self, period, close_data):
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

    def stoch_rsi(self, period, rsi_data, smooth, smooth2):
        stoch_rsi_data = []
        lowest, highest, stoch_rsi = 0, 0, 0
        x = 0
        while(rsi_data[x] == None):
            x +=1

        for i in range(0, period+x-1):
            stoch_rsi_data.append(None)

        for y in range(x, len(rsi_data)-period+1):
            highest = -1
            lowest = 101
            for day in range(y, y+period):
                if rsi_data[day] > highest:
                    highest = rsi_data[day]
                if rsi_data[day] < lowest:
                    lowest = rsi_data[day]
            
            if (highest - lowest) == 0:
                stoch_rsi_data.append(None)
            else:
                stoch_rsi = 100*((rsi_data[day] - lowest) / (highest - lowest))
                stoch_rsi_data.append(stoch_rsi)

        stoch_rsi_data = self.moving_average(stoch_rsi_data, smooth)
        # stoch_rsi_data = self.moving_average(stoch_rsi_data, smooth2)

        return stoch_rsi_data

    def mfi_execute(self, close_data, dates, high_data, low_data, volume_data, startAt, limit_top, limit_bottom):
        period = 17
        mfi_data = self.calculate_MFI(high_data, low_data, close_data, volume_data, period, dates)

        balances, b_dates, buyOrSell = [], [], [[],[]]
        self.balance = 100

        if startAt < period*2:
            start = 0
        else:
            start = startAt
            
        buy = close_data[start]
        amount = (self.balance - 0.002*self.balance)/buy
        print("")
        print("")
        print("")
        print("")
        print("starting balance -> mfi:knowing: ", self.calc_balance(buy, amount))
        self.calc_balance(buy, amount)
        balances.append(self.balance)
        b_dates.append(dates[start])
        print(dates[start], " [mfi:knowing] buy at ", close_data[start])

        for day in range(start, len(mfi_data)):
            buyOrSell[1].append(dates[day])
            #overbought = sell
            if mfi_data[day] < limit_top and mfi_data[day-1] > limit_top:
                buyOrSell[0].append("sell")

            #oversold = buy
            elif mfi_data[day] > limit_bottom and mfi_data[day-1] < limit_bottom:
                buyOrSell[0].append("buy")

            else:
                buyOrSell[0].append(None)


            #overbought = sell
            if ((mfi_data[day] < limit_top and mfi_data[day-1] > limit_top) or day == (len(mfi_data)-1)) and amount != 0:
                print(dates[day], " [mfi:knowing] sell at ", close_data[day], "       ", self.calc_balance(close_data[day], amount))
                self.calc_balance(close_data[day], amount)
                balances.append(self.balance)
                b_dates.append(dates[day])
                amount = 0

            #oversold = buy
            elif mfi_data[day] > limit_bottom and mfi_data[day-1] < limit_bottom and amount == 0:
                amount = (self.balance - 0.002*self.balance) / close_data[day]
                print(dates[day], " [mfi:knowing] buy at ", close_data[day])              

        return balances, b_dates, buyOrSell, mfi_data

    def rsi_execute(self, period, rsi_data, close_data, limit_top, limit_bottom, dates, startAt):
        balances, b_dates, buyOrSell = [], [], [[],[]]
        self.balance = 100
        lastBuyPrice = 0

        if startAt < period*2:
            start = 0
        else:
            start = startAt
            
        buy = close_data[start]
        amount = (self.balance - 0.002*self.balance)/buy
        """ print("")
        print("")
        print("")
        print("")
        print("starting balance -> stochRSI:knowing: ", self.calc_balance(buy, amount)) """
        self.calc_balance(buy, amount)
        balances.append(self.balance)
        b_dates.append(dates[start])
        """ print(dates[start], " [rsi:knowing] buy at ", close_data[start]) """

        for day in range(start, len(rsi_data)):
            buyOrSell[1].append(dates[day])
            #overbought = sell
            if rsi_data[day] < limit_top and rsi_data[day-1] > limit_top:
                buyOrSell[0].append("sell")

            #oversold = buy
            elif rsi_data[day] > limit_bottom and rsi_data[day-1] < limit_bottom:
                buyOrSell[0].append("buy")

            else:
                buyOrSell[0].append(None)


            #overbought = sell
            if ((rsi_data[day] < limit_top and rsi_data[day-1] > limit_top) or day == (len(rsi_data)-1)) and amount != 0:
            #if rsi_data[day] > limit_bottom and rsi_data[day-1] < limit_bottom:
                print(dates[day], " [rsi:knowing] sell at ", close_data[day], "       ", self.calc_balance(close_data[day], amount))
                self.calc_balance(close_data[day], amount)
                balances.append(self.balance)
                b_dates.append(dates[day])
                amount = 0

            #oversold = buy
            elif rsi_data[day] > limit_bottom and rsi_data[day-1] < limit_bottom and amount == 0:
            #elif rsi_data[day] < limit_bottom and rsi_data[day-1] > limit_bottom and amount == 0:
                amount = (self.balance - 0.002*self.balance) / close_data[day]
                print(dates[day], " [rsi:knowing] buy at ", close_data[day])              

        return balances, b_dates, buyOrSell

    def moving_average(self, close_data, period):
        average = []
        x = 0

        while close_data[x] == None:
            x += 1
            average.append(None)

        for i in range(x+1, x+period):
            average.append(None)

        for y in range(x, len(close_data)-(period-1)):
            sum = 0
            periodDivisor = period
            for x in range(y, y+period):
                if close_data[x] == None:
                    periodDivisor -= 1
                else:
                    sum += close_data[x]

            average.append(sum / periodDivisor)

        return average

    def ma_cross(self, av1, av2, dates=None):
        x = 0
        if dates == None:
            cross = []
        else:
            cross = [[],[]]
        cross.append(None)
        while av1[x] == None or av2[x] == None:
            x += 1
            cross.append(None)

        for y in range(x+1, len(av1)):
            #if av1 crosses av2 from below to top  = buy
            if av1[y] > av2[y] and av1[y-1] < av2[y-1]:
                if dates == None:
                    cross.append("buy")
                else:
                    cross[0].append("buy")
                    cross[1].append(dates[y])
            #if av1 falls below av2 = sell
            elif av1[y] < av2[y] and av1[y-1] > av2[y-1]:
                if dates == None:
                    cross.append("sell")
                else:
                    cross[0].append("sell")
                    cross[1].append(dates[y])
            else:
                if dates == None:
                    cross.append(None)
                else:
                    cross[0].append(None)
                    cross[1].append(dates[y])
        return cross

    def mAV_execute(self, cross, close_data, dates, startAt):
        balances, b_dates = [], []
        self.balance = 100
        amount = 0
        amount = (self.balance - 0.002*self.balance) / close_data[startAt]
        """ print("")
        print("")
        print("")
        print("")
        print("starting balance -> mAV:knowing: ", self.calc_balance(close_data[startAt], amount))
        print(dates[startAt], " [mAV:knowing] buy at ", close_data[startAt]) """
        self.calc_balance(close_data[startAt], amount)
        balances.append(self.balance)
        b_dates.append(dates[startAt])

        for day in range(startAt, len(cross)):
            #sell
            if ((cross[day] == "sell") or day == (len(cross)-1)) and amount != 0:
                #print(dates[day], " [mAV:knowing] sell at ", close_data[day], "       ", self.calc_balance(close_data[day], amount))
                self.calc_balance(close_data[day], amount)
                balances.append(self.balance)
                b_dates.append(dates[day])
                amount = 0
            
            #buy
            if cross[day] == "buy" and amount == 0:
                amount = (self.balance - 0.002*self.balance) / close_data[day]
                #print(dates[day], " [mAV:knowing] buy at ", close_data[day])

        return balances, b_dates

    def buy_or_sell(self, rsi_data, limit_top, limit_bottom, dates, start, end=None):
        buyOrSell = [[],[]]
        
        if end == None:
            for day in range(start, len(rsi_data)):
                buyOrSell[1].append(dates[day])
                #overbought = sell
                if rsi_data[day] < limit_top and rsi_data[day-1] > limit_top:
                    buyOrSell[0].append("sell")

                #oversold = buy
                elif rsi_data[day] > limit_bottom and rsi_data[day-1] < limit_bottom:
                    buyOrSell[0].append("buy")

                else:
                    buyOrSell[0].append(None)
        else:
            for day in range(start, end):
                buyOrSell[1].append(dates[day])
                #overbought = sell
                if rsi_data[day] < limit_top and rsi_data[day-1] > limit_top:
                    buyOrSell[0].append("sell")

                #oversold = buy
                elif rsi_data[day] > limit_bottom and rsi_data[day-1] < limit_bottom:
                    buyOrSell[0].append("buy")

                else:
                    buyOrSell[0].append(None)
        return buyOrSell
        """ #overbought = sell
        if rsi_data[len(rsi_data)-1] < limit_top and rsi_data[len(rsi_data)-2] > limit_top:
            return "sell", dates[len(dates)-1]

        #oversold = buy
        elif rsi_data[len(rsi_data)-1] > limit_bottom and rsi_data[len(rsi_data)-2] < limit_bottom:
            return "buy", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1] """

    def calculate_MFI(self, high_data, low_data, close_data, volume_data, period, dates=None):
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
            MFI.append(100- ( 100 / (1 + MFRatio )))

        return MFI

    def MFI_typicalPrice(self, close_data, high_data, low_data, day):
        return (high_data[day]+low_data[day]+close_data[day])/3

    def buy_or_sell_MFI(self, mfi, limitLow, limitHigh, dates):
        #overbought = sell
        if mfi[len(mfi)-1] < limitHigh and mfi[len(mfi)-2] > limitHigh:
            return "sell", dates[len(dates)-1]

        #oversold = buy
        elif mfi[len(mfi)-1] > limitLow and mfi[len(mfi)-2] < limitLow:
            return "buy", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1]

    def call_simulation(self, close_data, dates, close_data_mAV, dates_mAV, start, start_mAV, low_data, high_data):
        rsi_calculation, mAV_calculation = [], []
        
        print("")
        print("")
        print("")
        print("")

        rsi_calculation = self.call_rsi(close_data, dates, start)
        #mAV_calculation = self.call_mAV(close_data_mAV, dates_mAV, start_mAV)
        mAV_calculation = self.call_mAV(close_data, dates, start)

        balance_combined = [[],[]] 
        balance_combined = self.combined(close_data, dates, rsi_calculation[3], mAV_calculation[2], start, low_data, high_data)

        #return rsi_balances,       rsi_b_dates,        mAV_balances,       mAV_b_dates,        rsi_data,           balance_combined
        return rsi_calculation[0], rsi_calculation[1], mAV_calculation[0], mAV_calculation[1], rsi_calculation[2], balance_combined
        #return mAV_calculation[2]
    
    def call_rsi(self, close_data, dates, start):
        sell_or_buy, c_data, rsi_balances, rsi_b_dates = [], [], [], []
        rsi_amount = 0
        rsi_balance = 100

        rsi_bORs = [[],[]]

        rsi_data = [[],[]]

        rsi_amount = (rsi_balance - 0.002*rsi_balance) / close_data[start]
        """ print("starting balance -> stochRSI: ", rsi_amount*close_data[start])
        print(dates[start], "  [rsi] buy at ", close_data[start]) """
        rsi_balances.append(rsi_amount*close_data[start])
        rsi_b_dates.append(dates[start])

        for day in range(start, len(close_data)+1):
            c_data = close_data[:day]
            d_data = dates[:day]
            
            sell_or_buy = self.simulate_rsi(c_data, d_data)  
            rsi_data[0].append(sell_or_buy[1]) 
            rsi_data[1].append(d_data[len(d_data)-1])

            rsi_bORs[0].append(sell_or_buy[0])
            rsi_bORs[1].append(d_data[len(d_data)-1])

            #rsi
            if sell_or_buy[0] == "buy" and rsi_amount == 0:
                rsi_amount = (rsi_balance - 0.002*rsi_balance) / c_data[len(c_data)-1]
                """ print(d_data[len(d_data)-1], "  [rsi] buy at ", c_data[len(c_data)-1]) """
            elif (sell_or_buy[0] == "sell" or day == len(close_data)) and rsi_amount != 0:
                rsi_balance = rsi_amount * c_data[len(c_data)-1]
                rsi_amount = 0
                rsi_balances.append(rsi_balance)
                rsi_b_dates.append(d_data[len(d_data)-1])
                """ print(d_data[len(d_data)-1], "  [rsi] sell at ", c_data[len(d_data)-1], "          ", rsi_balance) """

        return rsi_balances, rsi_b_dates, rsi_data, rsi_bORs

    def call_MFI(self, close_data, dates, high_data, low_data, volume_data, start):
        sell_or_buy, c_data, mfi_balances, mfi_b_dates = [], [], [], []
        mfi_amount = 0
        mfi_balance = 100

        mfi_bORs = [[],[]]

        cross = []

        mfi_amount = (mfi_balance - 0.002*mfi_balance) / close_data[start]
        print("starting balance -> mfi: ", mfi_amount*close_data[start])
        print(dates[start], "  [mfi] buy at ", close_data[start])
        mfi_balances.append(mfi_amount*close_data[start])
        mfi_b_dates.append(dates[start])

        for day in range(start, len(close_data)+1):
            c_data = close_data[:day]
            d_data = dates[:day]
            h_data = high_data[:day]
            l_data = low_data[:day]
            v_data = volume_data[:day]

            sell_or_buy = self.simulate_MFI(c_data, h_data, l_data, v_data, d_data) 

            mfi_bORs[0].append(sell_or_buy)
            mfi_bORs[1].append(d_data[len(d_data)-1])

            #mfi 
            if sell_or_buy[0] == "buy" and mfi_amount == 0:
                mfi_amount = (mfi_balance - 0.002*mfi_balance) / c_data[len(c_data)-1]
                print(d_data[len(d_data)-1], "  [mfi] buy at ", c_data[len(c_data)-1])
            if (sell_or_buy[0] == "sell" or day == len(close_data)) and mfi_amount != 0:
                mfi_balance = mfi_amount * c_data[len(c_data)-1]
                mfi_amount = 0
                mfi_balances.append(mfi_balance)
                mfi_b_dates.append(d_data[len(d_data)-1])
                print(d_data[len(d_data)-1], "  [mfi] sell at ", c_data[len(d_data)-1], "          ", mfi_balance)

        return mfi_balances, mfi_b_dates, mfi_bORs

    def call_mAV(self, close_data, dates, start):
        sell_or_buy, c_data, mAV_balances, mAV_b_dates = [], [], [], []
        mAV_amount = 0
        mAV_balance = 100

        mAV_bORs = [[],[]]

        cross = []

        mAV_amount = (mAV_balance - 0.002*mAV_balance) / close_data[start]
        """ print("starting balance -> mAV: ", mAV_amount*close_data[start])
        print(dates[start], "  [mAV] buy at ", close_data[start]) """
        mAV_balances.append(mAV_amount*close_data[start])
        mAV_b_dates.append(dates[start])

        for day in range(start, len(close_data)+1):
            c_data = close_data[:day]
            d_data = dates[:day]
            
            sell_or_buy = self.simulate_mAV(c_data, d_data)  

            mAV_bORs[0].append(sell_or_buy)
            mAV_bORs[1].append(d_data[len(d_data)-1])

            #mAV 
            if sell_or_buy == "buy" and mAV_amount == 0:
                mAV_amount = (mAV_balance - 0.002*mAV_balance) / c_data[len(c_data)-1]
                """ print(d_data[len(d_data)-1], "  [mAV] buy at ", c_data[len(c_data)-1]) """
            if (sell_or_buy == "sell" or day == len(close_data)) and mAV_amount != 0:
                mAV_balance = mAV_amount * c_data[len(c_data)-1]
                mAV_amount = 0
                mAV_balances.append(mAV_balance)
                mAV_b_dates.append(d_data[len(d_data)-1])
                """ print(d_data[len(d_data)-1], "  [mAV] sell at ", c_data[len(d_data)-1], "          ", mAV_balance) """

        return mAV_balances, mAV_b_dates, mAV_bORs

    def simulate_rsi(self, close_data, dates):
        rsi_buyOrSell = None

        #rsi
        rsi = self.rsi(8, close_data)
        stoch_rsi = self.stoch_rsi(8, rsi, 3)

        rsi_buyOrSell = self.buy_or_sell(stoch_rsi, 0.5, 0.1)

        return rsi_buyOrSell

    def simulate_MFI(self, close_data, high_data, low_data, volume_data, dates):
        mfi_buyOrSell = None
        period = 14

        #mfi
        mfi = self.calculate_MFI(high_data, low_data, close_data, volume_data, period, dates)

        mfi_buyOrSell =  self.buy_or_sell_MFI(mfi, 20,80, dates)

        return mfi_buyOrSell

    def simulate_mAV(self, close_data, dates):
        mAV_buyOrSell = None
        
        #average
        averageShort = self.moving_average(close_data, 2)
        averageLong = self.moving_average(close_data, 21)

        cross = self.ma_cross(averageShort, averageLong)
        mAV_buyOrSell = cross[len(cross)-1]

        return mAV_buyOrSell

    def combined(self, close_data, dates, rsi_calculation, mAV_calculation, start, end, low_data, high_data, av):
        """
        combines RSI and mAV
        """

        self.balance = 100
        self.amount = 0
        rsi_index, mAV_index = 0, 0
        balance_combined = [[],[]]
        date = 0

        lastBuyPrice = 0

        print("")
        print("")
        print("test with combined rsi and mAV:")
        print("")

        self.amount = (self.balance - 0.002*self.balance) / close_data[start]
        balance_combined[0].append(self.balance)
        balance_combined[1].append(dates[start])
        self.balance = 0

        stopLoss = 0.05


        print("starting balance: ", self.amount*close_data[start])
        print(dates[start], "  buy at ", close_data[start])
        for idx in range(start, end):
            date = dates[idx]
            """ if high_data[idx] > lastBuyPrice:
                lastBuyPrice = high_data[idx] """

            try:
                rsi_index = rsi_calculation[1].index(date)
                mAV_index = mAV_calculation[1].index(date)
                av_i = av[1].index(date)
            except ValueError:
                pass  # do nothing!

            #if rsi_calculation[0][rsi_index] == "buy" and self.amount == 0 and av[0][av_i] > av[0][av_i-1]:
            if rsi_calculation[0][rsi_index] == "buy" and self.amount == 0:
                self.amount = (self.balance - 0.002*self.balance) / close_data[idx]
                lastBuyPrice = close_data[idx]
                print(dates[idx], "  buy at ", close_data[idx], " high would be: ", high_data[idx], " low would be: ", low_data[idx])


            #elif (mAV_calculation[0][mAV_index] == "sell" or dates[idx] == dates[len(dates)-1]) and self.amount != 0:
            elif (mAV_calculation[0][mAV_index] == "sell" or dates[idx] == dates[len(dates)-1] or ((lastBuyPrice/close_data[idx])-1) > stopLoss ) and self.amount != 0:
                if ((lastBuyPrice/close_data[idx])-1) > stopLoss:
                    self.balance = self.amount * (lastBuyPrice-lastBuyPrice*stopLoss)
                else:
                    self.balance = self.amount * close_data[idx]
                self.amount = 0
                balance_combined[0].append(self.balance)
                balance_combined[1].append(dates[idx])
                print(dates[idx], "  sell at ", close_data[idx], " high would be: ", high_data[idx], " low would be: ", low_data[idx], "          ", self.balance)

        return balance_combined

    def combinedMFI(self, close_data, dates, rsi_calculation, mav_calculation, start, end, low_data, high_data, mfi, av):
        """
        combines RSI and MFI
        """

        self.balance = 100
        self.amount = 0
        rsi_index, mfi_index = 0, 0
        balance_combined = [[],[]]
        date = 0
        lastBuyPrice = 0

        print("")
        print("")
        print("test with combined rsi and mfi:")
        print("")

        self.amount = (self.balance - 0.002*self.balance) / close_data[start]
        balance_combined[0].append(self.balance)
        balance_combined[1].append(dates[start])
        self.balance = 0
        
        stopLoss = 0.05

        print("starting balance: ", self.amount*close_data[start])
        print(dates[start], "  buy at ", close_data[start])
        
        for idx in range(start, end):
            date = dates[idx]

            try:
                rsi_index = rsi_calculation[1].index(date)
                mav_index = mav_calculation[1].index(date)
                mfi_i = mfi[1].index(date)
                av_i = av[1].index(date)
            except ValueError:
                pass  # do nothing!
            
            """ if high_data[idx] > lastBuyPrice:
                lastBuyPrice = high_data[idx] """

            #if (mfi[0][mfi_i] == "buy" or rsi_calculation[0][rsi_index] == "buy" ) and self.amount == 0 and av[0][av_i] > av[0][av_i-1]:
            if (rsi_calculation[0][rsi_index] == "buy" ) and self.amount == 0:
                self.amount = (self.balance - 0.002*self.balance) / close_data[idx]
                lastBuyPrice = close_data[idx]
                print(dates[idx], "  buy at ", close_data[idx], " high would be: ", high_data[idx], " low would be: ", low_data[idx])


            elif (mav_calculation[0][mav_index] == "sell" or dates[idx] == dates[len(dates)-1] or mfi[0][mfi_i] == "sell") and self.amount != 0:
            #elif (mav_calculation[0][mav_index] == "sell" or dates[idx] == dates[len(dates)-1] or ((lastBuyPrice/low_data[idx])-1) > stopLoss ) and self.amount != 0:

                """ if ((lastBuyPrice/low_data[idx])-1) > stopLoss:
                    self.balance = self.amount * (lastBuyPrice-lastBuyPrice*stopLoss)
                    print(dates[idx], "  sell at ", (lastBuyPrice-lastBuyPrice*stopLoss), " high would be: ", high_data[idx], " low would be: ", low_data[idx], "          ", self.balance)
                else: """
                self.balance = self.amount * close_data[idx]
                print(dates[idx], "  sell at ", close_data[idx], " high would be: ", high_data[idx], " low would be: ", low_data[idx], "          ", self.balance)
                self.amount = 0
                balance_combined[0].append(self.balance)
                balance_combined[1].append(dates[idx])
                

        return balance_combined

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

class Trader:
    def __init__(self, key, secret):
        self.helper = Helper(key, secret)
        self.test = Test()

    def calculate_mAV(self, close_data, period):
        average = []
        x = 0

        while close_data[x] == None:
            x += 1
            average.append(None)

        for i in range(x+1, x+period):
            average.append(None)

        for y in range(x, len(close_data)-(period-1)):
            sum = 0
            periodDivisor = period
            for x in range(y, y+period):
                if close_data[x] == None:
                    periodDivisor -= 1
                else:
                    sum += close_data[x]

            average.append(round(sum/periodDivisor, 4))

        return average

    def calculate_stochRSI(self, close_data, period, smooth, realClose):
        rsi_data, stoch_rsi_data = [], []
        lowest, highest, stoch_rsi, x = 0, 0, 0, 0

        rsi_data = self.calculate_rsi(close_data, period)

        while(rsi_data[x] == None):
            x +=1

        for i in range(0, period+x-1):
            stoch_rsi_data.append(None)

        for y in range(x, len(rsi_data)-period+1):
            highest = -1
            lowest = 101
            for day in range(y, y+period):
                if rsi_data[day] > highest:
                    highest = rsi_data[day]
                if rsi_data[day] < lowest:
                    lowest = rsi_data[day]
            
            if (highest - lowest) == 0:
                stoch_rsi_data.append(None)
            else:
                stoch_rsi = 100*((rsi_data[day] - lowest) / (highest - lowest))
                stoch_rsi_data.append(stoch_rsi)

        stoch_rsi_data = self.calculate_mAV(stoch_rsi_data, smooth)
        stoch_rsi_data = self.calculate_mAV(stoch_rsi_data, smooth)

        print("utc ", datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), " - stoch_rsi = ", stoch_rsi_data[len(stoch_rsi_data)-1], "current price ", round(realClose[len(realClose)-1]), "     ", end="", flush=True)

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
            pp[1].append(dates[i])

            curPP = pp[0][len(pp[0])-1]
            s1[0].append(2*curPP - maxV)
            s1[1].append(dates[i])

            s2[0].append(curPP - (maxV-minV))
            s2[1].append(dates[i])

            s3[0].append(curPP - 2*(maxV-minV))
            s3[1].append(dates[i])

            s4[0].append(((close[i-1]/1000 -(close[i-1]/1000)%1))*1000)
            s4[1].append(dates[i])

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

    def buyOrSellMAV(self, shortValue, longValue, close_data, dates):
        av_short = self.calculate_mAV(close_data[len(close_data)-shortValue-1:], shortValue)
        av_long = self.calculate_mAV(close_data[len(close_data)-longValue-1:], longValue)

        # #sys.stdout.flush()
        # #print("mav_short ", av_short[len(av_short)-1], " mav_long ", av_long[len(av_long)-1], end='      \r', flush=True)
        print("mav_short ", av_short[len(av_short)-1], " mav_long ", av_long[len(av_long)-1])

        #if av_short crosses av_long from below to top  = buy
        if av_short[len(av_short)-1] > av_long[len(av_long)-1] and av_short[len(av_short)-2] < av_long[len(av_long)-2]:
            return "buy", dates[len(dates)-1]

        #if av_short falls below av_long = sell
        elif av_short[len(av_short)-1] < av_long[len(av_long)-1] and av_short[len(av_short)-2] > av_long[len(av_long)-2]:
            return "sell", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1]

    def buyOrSellRSI(self, dates, limitLow, limitHigh, close_data, period, smooth, realClose, limitStop):
        rsi_data = self.calculate_stochRSI(close_data, period, smooth, realClose)
        
        #overbought = sell
        if rsi_data[len(rsi_data)-1] < limitHigh and rsi_data[len(rsi_data)-2] > limitHigh:
            return "sell", dates[len(dates)-1]

        #oversold = buy
        elif rsi_data[len(rsi_data)-1] > limitLow-limitStop and rsi_data[len(rsi_data)-2] < limitLow:
            return "buy", dates[len(dates)-1]

        else:
            return None, dates[len(dates)-1]

    def buyOrSellMFI(self, dates, limitLow, limitHigh, close_data, high_data, low_data, volume_data, period):
        MFI = self.calculate_MFI(high_data, low_data, close_data, volume_data, period)
        
        # sys.stdout.flush()
        print("mfi ", MFI[len(MFI)-1] ,"         ", end="", flush=True)

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
        
        print("resistance ", resistances[0][0][len(resistances[0][0])-1] ,"         ", end="", flush=True)
        print("support ", supports[0][0][len(supports[0][0])-1] ,"         ", end="", flush=True)

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

    def buyOrSellCOMB(self, open_data, high_data, low_data, close_data, volume_data, dates, shortValue, longValue, limitLow, limitHigh, period, smooth, limitStop, stopLoss, realClose, ash_c, ash_o, ash_d):
        buyOrSellMAV, buyOrSellRSI, buyOrSellMFI, buyEnabled = "", "", "", True
        
        close_data = close_data[:len(close_data)-1]
        dates = dates[:len(dates)-1]
        high_data = high_data[:len(high_data)-1]
        low_data = low_data[:len(low_data)-1]
        volume_data = volume_data[:len(volume_data)-1]

        # buyOrSellRSI = self.buyOrSellRSI(dates, limitLow, limitHigh, close_data, period, smooth, realClose, limitStop)
        buyOrSellRSI = self.buyOrSellRSI(dates, limitLow, limitHigh, open_data, period, smooth, realClose, limitStop) # --> calculate rsi with current open data (that's why the list is not edited above)
        buyOrSellMFI = self.buyOrSellMFI(dates, 15, 85, close_data, high_data, low_data, volume_data, 33)
        buyOrSellRES_SUP = self.buyOrSellResSup(ash_c, ash_d, ash_o, open_data)
        buyOrSellMAV = self.buyOrSellMAV(shortValue, longValue, close_data, dates)

        # lastBuyPrice = self.requestHistOrders('tBTCUSD')
        f = open("lastBuyPrice.txt", "r")
        textPrice = f.read()
        f.close()
        lastBuyPrice = float(textPrice)

        #open and read the file after the appending:
        f = open("buyEnabled.txt", "r")
        text = f.read()
        f.close()
        if text == 'True':
            buyEnabled = True
        else:
            buyEnabled = False

        if buyOrSellMAV[0] == "buy":
            # enable the possibility to buy
            f = open("buyEnabled.txt", "w")
            f.write("True")
            f.close()
            buyEnabled = True

# buy logic
        if (buyEnabled and not buyOrSellRES_SUP[0] == "sell" and buyOrSellRSI[0] == "buy"
            or buyOrSellRES_SUP[0] == "buy" 
           ):

            balance = self.calcBalance('tBTCUSD', 1)[0]
            if balance > 0.0:
                print("")
                print("")
                if buyOrSellRSI[0] == "buy": 
                    print("RSI signal == buy")
                elif buyOrSellRES_SUP[0] == "buy":
                    print("RESISTANCE signal == buy")

                print("available balance = ", balance)
                print("utc ", datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), "  buy at ", realClose[len(realClose)-1], " ash high would be: ", high_data[len(high_data)-1], " ash low would be: ", low_data[len(low_data)-1])
                self.executeBuy(balance)
                print("")

# sell logic
        elif ( buyOrSellMAV[0] == "sell" 
            or buyOrSellMFI[0] == "sell" 
            or buyOrSellRES_SUP[0] == "sell"
            or ((lastBuyPrice/realClose[len(realClose)-1])-1) > stopLoss
            ):
            amount = self.calcBalance('tBTCUSD', -1)[0]
            if amount < -0.001:
                # get balance after sell
                print("")
                print("")

                if buyOrSellMAV[0] == "sell": 
                    print("MAV signal == sell")
                elif buyOrSellMFI[0] == "sell":
                    print("MFI signal == sell")
                elif buyOrSellRES_SUP[0] == "sell":
                    print("SUPPORT signal == sell")
                elif (newCandle and ((lastBuyPrice/realClose[len(realClose)-1])-1) > stopLoss):
                    print("stop loss executed!")

                    #disable the possibility to buy
                    f = open("buyEnabled.txt", "w")
                    f.write("False")
                    f.close()
                    buyEnabled = False

                print("amount available to sell = ", amount)
                print("utc ", datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), "  sell at ", realClose[len(realClose)-1], " ash high would be: ", high_data[len(high_data)-1], " ash low would be: ", low_data[len(low_data)-1])
                self.executeSell(amount)
                print("")
        pass 

    def calcBalance(self, symbol, buy_or_sell):
        """
        buy_or_sell 
        1 == buy 
        -1 == sell
        """
        endpoint = "v2/auth/calc/order/avail"
        payload = {
            "symbol": 'tBTCUSD',
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

    def requestHistOrders(self, symbol):
        payload = {
            "limit": 15
        }

        response = self.helper.req("v2/auth/r/orders/" + symbol + "/hist", payload)
        # loop over items
        # check 07 for a positive amount -> only last BUY price wanted
        # check 17 for price
        if response.status_code == 200:
            r = response.json()

            for trade in r:
                if trade[7] > 0:
                    return float(trade[17])
        else:
          print('error while requesting hist orders, status_code = ', response.status_code, response.text)
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
    
    def executeBuy(self, balance): 
        price = self.getTicker('tBTCUSD')

        if balance >= 25.0:
            amount = balance / price[6]
            print("try to buy an amount of ", amount, " at a price of ", price[6])
            order_response = self.submit_order('tBTCUSD', price[6], amount)

            try:
                if order_response[0] == 'error':
                    if order_response[1] == 10001:
                        print(order_response[2])
                        Trader.executeBuy(self, balance-0.1)
                    else:
                        print("uncaught error")
                        print(order_response[3])
                elif order_response[6] == 'SUCCESS':
                    order_id = order_response[4][0][2]
                    status = order_response[4][0][13]
                    print("Order : ", order_id, " with status: ", status)

                    f = open("writeLastBuyPrice.txt", "w")
                    f.write("True")
                    f.close()
            except:
                print(order_response[2])
                Trader.executeBuy(self, balance-0.1)

    def executeSell(self, amount):
        price = self.getTicker('tBTCUSD')
        print("last price ", price[6])

        order_response = self.submit_order('tBTCUSD', price[6], amount)

        try:
            if order_response[0] == 'error':
                print("uncaught error")
                print(order_response[2])
                Trader.executeSell(self, amount+0.00001)

            elif order_response[6] == 'SUCCESS':
                order_id = order_response[4][0][2]
                status = order_response[4][0][13]
                print("Order : ", order_id, " with status: ", status)
        except:
            print("uncaught error in try")
            print(order_response[2])
            Trader.executeSell(self, amount+0.00001)

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
    def __init__(self, key, secret):
        self.trader = Trader(key, secret)
        self.balance = 100
        self.amount = 0

    def buyOrSellTest(self, close_data, high_data, low_data, volume_data, dates, shortValue, longValue, limitLow, limitHigh, period, smooth, stopLoss, realOpen, ash_c, ash_o, ash_d):
        start = 330
        lastBuyPrice = 0
        balance_combined = [[],[]]
        writelastBuyPrice = False

        cl = close_data
        hi = high_data
        lo = low_data
        vol = volume_data
        rOp = realOpen
        d = dates

        ash_close = ash_c
        ash_open = ash_o
        ash_dates = ash_d
        buyEnabled = True
        
        balance_combined[0].append(self.getAvailBalance())
        balance_combined[1].append(dates[start])

        for idx in range(start,len(cl)):
            
            close_data = cl[:idx+1]
            dates = d[:idx+1] 
            high_data = hi[:idx+1]
            low_data = lo[:idx+1]
            volume_data = vol[:idx+1]
            realOpen = rOp[:idx+1]

            ash_c = ash_close[:idx]
            ash_o = ash_open[:idx]
            ash_d = ash_dates[:idx]
            
            #adjust to have only data that can be known
            close_data = close_data[:len(close_data)-1]
            high_data = high_data[:len(high_data)-1]
            low_data = low_data[:len(low_data)-1]
            volume_data = volume_data[:len(volume_data)-1]
            
            ash_c = ash_c[:len(ash_c)-1]

            if writelastBuyPrice:
                lastBuyPrice = low_data[len(low_data)-1]
                writelastBuyPrice = False

            buyOrSellRSI = self.trader.buyOrSellRSI(dates, limitLow, limitHigh, realOpen, period, smooth, realOpen, 0)
            buyOrSellMFI = self.trader.buyOrSellMFI(dates, 15, 85, close_data, high_data, low_data, volume_data, 33)
            buyOrSellRES_SUP = self.trader.buyOrSellResSup(ash_c, ash_d, ash_o, realOpen)
            buyOrSellMAV = self.trader.buyOrSellMAV(shortValue, longValue, close_data, dates)

            if buyOrSellMAV[0] == "buy":
                buyEnabled = True

            if ( buyEnabled and not buyOrSellRES_SUP[0] == "sell" 
                and buyOrSellRSI[0] == "buy" 
                or buyOrSellRES_SUP[0] == "buy"
                ) and self.getAvailBalance() >= 20.0:

                self.simulate_buy(self.calcMaxAmount(realOpen[idx]), realOpen[idx])
                writelastBuyPrice = True

                if(buyOrSellRSI[0] == "buy"):
                    print(dates[idx], "  RSI buy at open ", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "                                                         ")
                if(buyOrSellRES_SUP[0] == "buy"):
                    print(dates[idx], "  RESISTANCE buy at open ", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "                                                         ")

                balance_combined[0].append(self.getWalletBalance(realOpen[idx]))
                balance_combined[1].append(dates[idx])

            elif (buyOrSellMAV[0] == "sell" 
                or buyOrSellMFI[0] == "sell" 
                or buyOrSellRES_SUP[0] == "sell"
                or idx == len(cl)-1 
                or ((lastBuyPrice/realOpen[idx])-1) > stopLoss 
                ) and self.getAvailAmount() > 0.0:
                
                self.simulate_sell(self.getAvailAmount(), realOpen[idx])
                balance = self.getWalletBalance(realOpen[idx])
                
                if ((lastBuyPrice/realOpen[idx])-1) > stopLoss:
                    print(dates[idx], "  STOPLOSS sell at open", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "          ", balance, "                                 ")
                    buyEnabled = False
                else:
                    if(buyOrSellMAV[0] == "sell"):
                        print(dates[idx], "  MAV sell at open", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "          ", balance, "                                  ")
                    if(buyOrSellMFI[0] == "sell"):
                        print(dates[idx], "  MFI sell at open", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "          ", balance, "                                  ")
                    if(buyOrSellRES_SUP[0] == "sell"):
                        print(dates[idx], "  SUPPORT sell at open", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "          ", balance, "                                  ")
                    if(idx == len(cl)-1):
                        print(dates[idx], "  FIN sell at open", realOpen[idx], " high would be: ", high_data[idx-1], " low would be: ", low_data[idx-1], "          ", balance, "                                  ")

                print("")
                balance_combined[0].append(self.getWalletBalance(realOpen[idx]))
                balance_combined[1].append(dates[idx])
        return balance_combined

    def simulate_buy(self, amount, price):
        if(self.getAvailBalance() > 0 and self.getAvailBalance() >= (amount * price / 0.998)):
            self.setAvailBalance(round(self.getAvailBalance() - (amount * price / 0.998),5))
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
        return round(((0.998 * self.getAvailBalance()) / price), 5)

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

class Client:
    """
    Client for the bitfinex.com API.

    See https://www.bitfinex.com/pages/api for API documentation.
    """

    def server(self, version=VERSION):
        return u"{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, version)


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

    def _get(self, url):
        return requests.get(url, timeout=TIMEOUT).json()


    def _build_parameters(self, parameters):
        # sort the keys so we can test easily in Python 3.3 (dicts are not
        # ordered)
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])


    def symbols(self):
        """
        GET /symbols

        curl https://api.bitfinex.com/v1/symbols
        ['btcusd','ltcusd','ltcbtc']
        """
        return self._get(self.url_for(PATH_SYMBOLS))


    def ticker(self, symbol):
        """
        GET /ticker/:symbol

        curl https://api.bitfinex.com/v1/ticker/btcusd
        {
            'ask': '562.9999',
            'timestamp': '1395552290.70933607',
            'bid': '562.25',
            'last_price': u'562.25',
            'mid': u'562.62495'}
        """
        data = self._get(self.url_for(PATH_TICKER, (symbol)))

        # convert all values to floats
        return self._convert_to_floats(data)


    def today(self, symbol):
        """
        GET /today/:symbol

        curl "https://api.bitfinex.com/v1/today/btcusd"
        {"low":"550.09","high":"572.2398","volume":"7305.33119836"}
        """

        data = self._get(self.url_for(PATH_TODAY, (symbol)))

        # convert all values to floats
        return self._convert_to_floats(data)


    def stats(self, symbol):
        """
        curl https://api.bitfinex.com/v1/stats/btcusd
        [
            {"period":1,"volume":"7410.27250155"},
            {"period":7,"volume":"52251.37118006"},
            {"period":30,"volume":"464505.07753251"}
        ]
        """
        data = self._get(self.url_for(PATH_STATS, (symbol)))

        for period in data:

            for key, value in period.items():
                if key == 'period':
                    new_value = int(value)
                elif key == 'volume':
                    new_value = float(value)

                period[key] = new_value

        return data


    def lendbook(self, currency, parameters=None):
        """
        curl "https://api.bitfinex.com/v1/lendbook/btc"

        {"bids":[{"rate":"5.475","amount":"15.03894663","period":30,"timestamp":"1395112149.0","frr":"No"},{"rate":"2.409","amount":"14.5121868","period":7,"timestamp":"1395497599.0","frr":"No"}],"asks":[{"rate":"6.351","amount":"15.5180735","period":5,"timestamp":"1395549996.0","frr":"No"},{"rate":"6.3588","amount":"626.94808249","period":30,"timestamp":"1395400654.0","frr":"Yes"}]}

        Optional parameters

        limit_bids (int): Optional. Limit the number of bids (loan demands) returned. May be 0 in which case the array of bids is empty. Default is 50.
        limit_asks (int): Optional. Limit the number of asks (loan offers) returned. May be 0 in which case the array of asks is empty. Default is 50.
        """
        data = self._get(self.url_for(PATH_LENDBOOK, path_arg=currency, parameters=parameters))

        for lend_type in data.keys():

            for lend in data[lend_type]:

                for key, value in lend.items():
                    if key in ['rate', 'amount', 'timestamp']:
                        new_value = float(value)
                    elif key == 'period':
                        new_value = int(value)
                    elif key == 'frr':
                        new_value = value == 'Yes'

                    lend[key] = new_value

        return data

    
    def order_book(self, symbol, parameters=None):
        """          curl "https://api.bitfinex.com/v1/book/btcusd"

        {"bids":[{"price":"561.1101","amount":"0.985","timestamp":"1395557729.0"}],"asks":[{"price":"562.9999","amount":"0.985","timestamp":"1395557711.0"}]}

        The 'bids' and 'asks' arrays will have multiple bid and ask dicts.

        Optional parameters

        limit_bids (int): Optional. Limit the number of bids returned. May be 0 in which case the array of bids is empty. Default is 50.
        limit_asks (int): Optional. Limit the number of asks returned. May be 0 in which case the array of asks is empty. Default is 50.

        eg.
        curl "https://api.bitfinex.com/v1/book/btcusd?limit_bids=1&limit_asks=0"
        {"bids":[{"price":"561.1101","amount":"0.985","timestamp":"1395557729.0"}],"asks":[]}

        """
        
        data = self._get(self.url_for(PATH_ORDERBOOK, path_arg=symbol, parameters=parameters))

        for type_ in data.keys():
            for list_ in data[type_]:
                for key, value in list_.items():
                    list_[key] = float(value)

        return data

    def _convert_to_floats(self, data):
        """
        Convert all values in a dict to floats
        """
        for key, value in enumerate(data):
            data[key] = float(value)

        return data