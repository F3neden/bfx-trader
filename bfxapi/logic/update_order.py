import os
import sys
import configparser
sys.path.append('../../../')

from bfxapi import Client, Order

credentials = configparser.ConfigParser()
credentials.read('bfxapi/config/credentials.ini')
API_KEY = credentials['TRADER']['API_KEY']
API_SECRET = credentials['TRADER']['API_SECRET']

bfx = Client(
  API_KEY=API_KEY,
  API_SECRET=API_SECRET,
  logLevel='DEBUG'
)

@bfx.ws.on('order_update')
def order_updated(order):
  print ("Order updated.")
  print (order)

@bfx.ws.once('order_update')
async def order_once_updated(order):
  # update a second time using the object function
  await order.update(price=80, amount=0.02, flags="2nd update")

@bfx.ws.once('order_confirmed')
async def trade_completed(order):
  print ("Order confirmed.")
  print (order)
  await bfx.ws.update_order(order.id, price=100, amount=0.01)

@bfx.ws.on('error')
def log_error(msg):
  print ("Error: {}".format(msg))

@bfx.ws.once('authenticated')
async def submit_order(auth_message):
  # create an inital order a really low price so it stays open
  await bfx.ws.submit_order('tBTCUSD', 10, 1, Order.Type.EXCHANGE_LIMIT)

bfx.ws.run()
