from os import readlink
import sys
import subprocess
import telegram
from telegram import Update, ParseMode
from telegram.ext import CommandHandler, Updater, CallbackContext
import datetime
import time
import html
import traceback
import pickle
import logging
import configparser

class TelegramBot:
    def __init__(self) -> None:
        credentials = configparser.ConfigParser()
        credentials.read('bfxapi/config/credentials.ini')
        self.token = credentials['TelegramMain']['Token']
        self.chatId = credentials['TelegramMain']['Chat_Id']

        self.p = type('subprocess.Popen', (), {})()
        self.timestamp_start=datetime.datetime.now()
        updater = Updater(token=self.token)
        self.dispatcher = updater.dispatcher
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
        )

        self.logger = logging.getLogger(__name__)

        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('stop', self.stop))
        self.dispatcher.add_handler(CommandHandler('restart', self.restart))
        self.dispatcher.add_handler(CommandHandler('stats', self.stats))
        self.dispatcher.add_handler(CommandHandler('active', self.active))
        self.dispatcher.add_handler(CommandHandler('help', self.help))
        self.dispatcher.add_error_handler(self.error_handler)

        updater.start_polling()

        self.setIsStopped(False)

        # #clear data.txt
        # f = open("data.txt","w")
        # f.close()

    def start(self, update, context):
        self.starter()

    def stop(self, update, context):
        self.stopper()
    
    def restart(self, update, context):
        self.rebooter()

    def stats(self, update, context):
        context.bot.send_message(chat_id=self.chatId, text=self.getStatsMessage())

    def active(self, update, context):
        self.checkIfActive()

    def help(self, update, context):
        s = 'You can control the bot with the following commands:\n'
        s += '/start' + '\n'
        s += '/stop' + '\n'
        s += '/restart' + '\n'
        s += '/stats' + '\n'
        s += '/active' + '\n'
        context.bot.send_message(chat_id=self.chatId, text=s)

    def sendMsg(self, msg):
        bot = telegram.Bot(self.token)
        bot.send_message(self.chatId, msg)

#### helper
    def restarter(self):
        self.stopper()
        time.sleep(1)
        self.starter()

    def starter(self):
        self.p = subprocess.Popen([sys.executable, 'trader.py'])
        self.sendMsg("Bot started!")
        print("Bot started!")
        self.setIsStopped(False)

    def stopper(self):
        try:
            self.p.terminate()
            self.sendMsg("Bot stopped!")
            print("Bot stopped")
            self.setIsStopped(True)
            self.checkIfActive()
        except Exception as e:
            print(e)
            self.sendMsg("Error while stopping!")

    def getStatsMessage(self):
        file = open("data.txt", "r")
        l = file.readlines()
        file.close()
        stats = ""

        x = len(l)-1
        while( x > 0):
            stats = l[x] + stats
            x -= 1

        result = "CURRENT " + str(datetime.datetime.now().replace(microsecond=0)) + "\n"
        result += "STARTUP " + str(self.timestamp_start.replace(microsecond=0)) + "\n"
        result += "UPTIME " + str(datetime.datetime.now().replace(microsecond=0)-self.timestamp_start.replace(microsecond=0)) + "\n"
        result += stats
        return result

    def checkIfActive(self):
        try:
            poll = self.p.poll()
            if poll is None:
                self.sendMsg("Subprocess is still active! IsStopped = " + self.getIsStopped())
            else:
                self.sendMsg("Subprocess was terminated!  IsStopped = " + self.getIsStopped())
        except Exception as e:
            print(e)
            self.sendMsg("Error while checking for activity!")

    def error_handler(self, update: Update, context: CallbackContext):
        """Log the error and send a telegram message to notify the developer."""
        # Log the error before we do anything else, so we can see it even if something breaks.
        self.logger.error(msg="Exception while handling an update:", exc_info=context.error)

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)

        message = (
            f'An exception was raised while handling an update\n'
            f'<pre>{html.escape(tb_string)}</pre>'
        )

        context.bot.send_message(chat_id=self.chatId, text=message, parse_mode=ParseMode.HTML)

    def setIsStopped(self, status):
        f = open("isStopped.txt", "w")
        f.write(str(status))
        f.close()

    def getIsStopped(self):
        f = open("isStopped.txt", "r")
        text = f.read()
        f.close()
        return text

print("Telegram Bot started")
telegramMainBot = TelegramBot()
telegramMainBot.starter()

previous = ""
while 1:
    time.sleep(600)
    fp = open("shared.pkl", "rb")
    shared = pickle.load(fp)

    f = open("isStopped.txt", "r")
    text = f.read()
    f.close()

    if shared["Date"] == previous and text == "False":
        telegramMainBot.sendMsg("The bot did not receive any updates. I have restarted it!")
        telegramMainBot.rebooter()
    previous = shared["Date"]