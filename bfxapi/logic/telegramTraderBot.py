import sys
import telegram
from telegram import Update, ParseMode
from telegram.ext import CommandHandler, Updater, CallbackContext
import traceback
import html
import logging
import json
import configparser
sys.path.append('../../')

#for balance hist pic
from datetime import datetime
import pandas as pd


class TelegramBot:
    def __init__(self) -> None:
        try:
            self.trader = type('class', (), {})()
            
            credentials = configparser.ConfigParser()
            credentials.read('bfxapi/config/credentials.ini')
            self.token = credentials['TelegramTrader']['Token']
            self.chatId = credentials['TelegramTrader']['Chat_Id']

            updater = Updater(token=self.token)
            self.dispatcher = updater.dispatcher

            logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
            )
            
            self.logger = logging.getLogger(__name__)

            start_handler = CommandHandler('newChat', self.newChat)
            sell_handler = CommandHandler('sell', self.sell)
            buy_handler = CommandHandler('buy', self.buy)
            enableBuy_handler = CommandHandler('enableBuy', self.enableBuy)
            disableBuy_handler = CommandHandler('disableBuy', self.disableBuy)
            histOrders_handler = CommandHandler('histOrders', self.histOrders)
            balance_handler = CommandHandler('balance', self.balance)
            self.dispatcher.add_handler(CommandHandler('help', self.help))
            self.dispatcher.add_handler(start_handler)
            self.dispatcher.add_handler(sell_handler)
            self.dispatcher.add_handler(buy_handler)
            self.dispatcher.add_handler(enableBuy_handler)
            self.dispatcher.add_handler(disableBuy_handler)
            self.dispatcher.add_handler(histOrders_handler)
            self.dispatcher.add_handler(balance_handler)
            self.dispatcher.add_error_handler(self.error_handler)

            updater.start_polling()

            with open('bfxapi/config/config.json', 'r') as f:
                config = json.load(f)

            self.symbol = 't'+config['GENERAL']['SYMBOL']

            self.sendInfo("trader bot started!")
        except Exception as e:
            print("error in init method: ", e)
            self.sendWarning(e)

    def error_handler(self, update: Update, context: CallbackContext):
        """Log the error and send a telegram message to notify the developer."""
        # Log the error before we do anything else, so we can see it even if something breaks.
        self.logger.error(msg="Exception while handling an update:", exc_info=context.error)

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096 character limit.
        message = (
            f'An exception was raised while handling an update\n'
            # f'<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}'
            # '</pre>\n\n'
            # f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
            # f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
            f'<pre>{html.escape(tb_string)}</pre>'
        )

        # Finally, send the message
        context.bot.send_message(chat_id=self.chatId, text=message, parse_mode=ParseMode.HTML)

    def help(self, update, context):
        s = 'You can control the bot with the following commands:\n'
        s += '/newChat' + '\n'
        s += '/sell' + '\n'
        s += '/buy' + '\n'
        s += '/enableBuy' + '\n'
        s += '/disableBuy' + '\n'
        s += '/histOrders' + '\n'
        s += '/balance' + '\n'
        context.bot.send_message(chat_id=self.chatId, text=s)

    def newChat(self, update, context):
        self.chatId = update.effective_chat.id
        print("new chatId: ", self.chatId)
        context.bot.send_message(chat_id=self.chatId, text="I'm a bot, please talk to me!")
        print("bot started!")

    def sell(self, update, context):
        print("Sell initiated from Telegram!")
        amount = self.trader.calcBalance(self.symbol, -1)[0]
        self.trader.executeSell(amount)

    def buy(self, update, context):
        print("Buy initiated from Telegram!")
        balance = self.trader.calcBalance(self.symbol, 1)[0]
        self.trader.executeBuy(balance)
        
    def enableBuy(self, update, context):
        print("Enabling buy initiated from Telegram!")
        f = open("buyEnabled.txt", "w")
        f.write("True")
        f.close()

    def disableBuy(self, update, context):
        print("Disabling buy initiated from Telegram!")
        f = open("buyEnabled.txt", "w")
        f.write("False")
        f.close()

    def balance(self, update, context):
        balance = self.trader.calcBalance(self.symbol, 1)[0]
        amount = abs(self.trader.calcBalance(self.symbol, -1)[0])
        price = self.trader.getTicker(self.symbol)[6]

        currentBalance = "Current Balance: ", balance + amount * price
        context.bot.send_message(chat_id=self.chatId, text=currentBalance)

    def histOrders(self, update, context):
        dt_obj = datetime.strptime('01.03.2020 00:00:00,00',
                           '%d.%m.%Y %H:%M:%S,%f')
        millisec = dt_obj.timestamp() * 1000

        balance = self.trader.calcBalance(self.symbol, 1)[0]
        amount = abs(self.trader.calcBalance(self.symbol, -1)[0])
        price = self.trader.getTicker(self.symbol)[6]

        currentBalance = balance + amount * price

        histTrades = self.trader.requestHistTrades(self.symbol, millisec)
        df = pd.DataFrame(columns =['Date', 'Amount', 'Price'])

        for trade in histTrades:
            df = df.append({'Date': str(pd.to_datetime(int(trade[2]) / 1000, unit='s')), 'Amount': trade[4], 'Price': trade[5]}, ignore_index=True)

        dfBalance = pd.DataFrame(columns =['Date', 'Balance'])
        dfBalance = dfBalance.append({'Date': str(datetime.now()), 'Balance': abs(round(currentBalance,2))},ignore_index=True)
        for i, row in df.iterrows():
            if abs(row['Amount']) > 0.001:
                dfBalance = dfBalance.append({'Date': row['Date'], 'Balance': abs(round(row['Amount'] * row['Price'],2))},ignore_index=True)
        
        # print(dfBalance.to_string())

        import matplotlib
        matplotlib.use('Agg')
        import pylab
        pylab.plot(dfBalance["Date"][::-1].tolist(), dfBalance["Balance"][::-1].tolist(), linestyle='-', scalex=True)
        pylab.savefig('histBalance.png')

        context.bot.send_document(chat_id=self.chatId, document=open('histBalance.png', 'rb'))

    def sendMsg(self, msg, chatId):
        try:
            bot = telegram.Bot(self.token)
            bot.send_message(chatId, str(msg))
        except Exception as e:
            print("error in sendMsg method: ", e)

    def sendInfo(self, msg):
        self.sendMsg(msg, '1574879391')
        return msg

    def sendWarning(self, msg):
        self.sendMsg(msg, '-584881214')
        return msg