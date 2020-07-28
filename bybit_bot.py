#!/usr/bin/env python
# coding: utf-8

import pickle
from datetime import datetime
from bybit import bybit
import warnings
warnings.simplefilter("ignore")
import requests
import json
import os


from telegram import User, Update
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, PicklePersistence)

import logging


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY = range(2)

reply_keyboard = [['account'],['Done']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def usd_str(value):
    if '.' in str(value):
        if float(value) < 0:
            value = float(value)*-1
            value = '-'+"${:,.2f}".format(float(value))
        else:
            value = "${:,.2f}".format(float(value))
    else:
        if float(value) < 0:
            value = float(value)*-1
            value = '-'+"${:,}".format(float(value))
        else:
            value = "${:,}".format(float(value))
    return value

def btc_str(value):
    value = "{:,.8f}".format(float(value))
    return value

def pickle_write(file, item):
    with open(file, 'wb') as handle:
        pickle.dump(item, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return print(file+' saved')

def pickle_load(file):
    with open(file, 'rb') as handle:
        temp = pickle.load(handle)
    return temp

def dict_str(dict_item):
    if type(dict_item) == str:
        dict_msg = dict_item
    else:
        dict_msg = ''
        try:
            for x in range(len(dict_item)):
                for k, v in dict_item[x].items():
                    dict_msg += str(k)+': '+str(v)+'\n'
                dict_msg += '\n'
        except KeyError:
            for k, v in dict_item.items():
                dict_msg += str(k)+': '+str(v)+'\n'
        dict_msg = dict_msg[:dict_msg.rfind('\n')]
    return dict_msg

def y_n_prompt():
    while True:
        y_n_responses = ['Yes', 'No']
        for (x, y) in enumerate(y_n_responses):
            print(str(x)+': '+y)
        response = y_n_responses[int(input('> '))]
        if response not in y_n_responses:
            print('Invalid Selection'+'\n')
            continue
        else:
            break
    return response

def list_prompt(initial_dialogue, list_to_view):
    while True:
        try:
            print(initial_dialogue)
            for k, v in enumerate(list_to_view):
                print(str(k)+': '+v)
            resp = list_to_view[int(input('> '))]
        except (IndexError, ValueError):
            print('Selection out of range of acceptable responses'+'\n')
            continue
        else:
            print('Selection: '+str(resp)+'\n')
            break
    return resp

def list_to_dict(list_item):
    temp = {}
    for x,y in enumerate(list_item):
        temp[x+1] = y
    return temp

def load_credentials(account):
    file = 'credentials.pickle'
    exchange = 'Bybit'

    master_credentials = pickle_load(file)
    account = account
    temp_exchange = {k:v for k,v in master_credentials[exchange].items() if k == account}
    final_user = {exchange: dict(temp_exchange[account].items())}
    client = bybit(test=False,api_key=final_user[exchange]['api_key'],
                    api_secret=final_user[exchange]['api_secret']) 
    return client


def telegram_sendText(bot_credentials, bot_message):
    bot_token = bot_credentials[0]
    bot_chatID = bot_credentials[1]
    send_text = 'https://api.telegram.org/bot'+bot_token+'/sendMessage?chat_id='+bot_chatID+'&text='+bot_message
    response = requests.get(send_text)
    return response.json()

def load_bot():
    file = 'credentials.pickle'
    load_bot = False
    create_bot = False
    confirm_bot = False
    if os.path.exists(file):
        try:
            master_credentials = pickle_load(file)['bots']
        except KeyError:
            bot_name = str(input('Give your bot a name'+'\n'+'> '))
            master_credentials = pickle_load(file)
            master_credentials['bots'] = {bot_name: {'bot_token': None,
                                                     'bot_chatID': None}}
            create_bot = True
        else:
            master_credentials = pickle_load(file)
            load_bot = True
    else:
        bot_name = str(input('Give your bot a name'+'\n'+'> '))
        master_credentials = {'bots': {bot_name: {'bot_token': None,
                                                  'bot_chatID': None}}}
        create_bot = True
    if load_bot:
        bot_name = list(master_credentials['bots'].keys())
        bot_name = list_prompt('Choose your saved bot', bot_name+['New Bot'])
        if bot_name == 'New Bot':
            bot_name = str(input('Give your bot a name'+'\n'+'> '))
            create_bot = True
        else:
            credentials = master_credentials['bots'][bot_name]
            confirm_bot = True
    if confirm_bot:
        print('Confirm '+bot_name+' Connection')
        resp = y_n_prompt()
        if resp == 'No':
            print('Create new bot credentials')
            bot_name = str(input('Give your bot a name'+'\n'+'> '))
            create_bot = True            
    if create_bot:
        while True:
            bot_token = str(input('Input Your Telegram Bot API Key'+'\n'+'> '))
            bot_chatID = str(input('Input Your Telegram User ChatID'+'\n'+'> '))
            credentials = {'bots': {bot_name: {'bot_token': bot_token,
                                               'bot_chatID': bot_chatID}}}
            test_msg = telegram_sendText((bot_token, bot_chatID), 'Testing')['ok']
            if test_msg:
                print('\n'+'Confirm Test Message Receipt')
                resp = y_n_prompt()
                if resp == 'No':
                    print('Try Again'+'\n')
                    continue
                else:
                    print('Bot Credentials Verified'+'\n')
                    break
            else:
                print('Test Message Failed. Reenter Bot Credentials'+'\n')
                continue
    
        master_credentials['bots'].update(credentials['bots'])
        pickle_write(file, master_credentials)
    return master_credentials['bots'][bot_name]


file = 'credentials.pickle'
master_credentials = pickle_load(file)
temp_bot = {k:v for k,v in master_credentials.items() if k == 'bots'}
bot_accounts = list(temp_bot['bots'].keys())
bot_account = list_prompt('Choose a Telegram Bot', bot_accounts+['New Bot'])
if bot_account == 'New Bot':
    load_bot()
temp_bot = {k:v for k,v in temp_bot['bots'].items() if k == bot_account}
botAPI = temp_bot[bot_account]['bot_token']


def wallet_update(account):
    client = load_credentials(account);
    
    ACCOUNT = account
    LASTPRICE = float([x['last_price'] for x in requests.get('https://api.bybit.com/v2/public/tickers?symbol=BTCUSD').json()['result']][0])
    CURRENT_WALLET = client.Wallet.Wallet_getBalance(coin='BTC').result()[0]['result']['BTC']
    BALANCE = CURRENT_WALLET['wallet_balance']
    UPNL = CURRENT_WALLET['unrealised_pnl']
    UBALANCE = CURRENT_WALLET['equity']
    WALLETDICT = {'CurrentPrice': usd_str(LASTPRICE),
                'Account': ACCOUNT,
                'Balance': btc_str(BALANCE)+' | '+usd_str(BALANCE*LASTPRICE),
                'uPNL': btc_str(UPNL)+' | '+usd_str(UPNL*LASTPRICE),
                'uBalance': btc_str(UBALANCE)+' | '+usd_str(UBALANCE*LASTPRICE)}

    return WALLETDICT

def current_open(account):
    client = load_credentials(account);
    now = datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S')
    
    WALLETDICT = wallet_update(account);

    try:
        OPENPOSITION = [x for x in client.Positions.Positions_myPosition().result()[0]['result'] if x['symbol'] == 'BTCUSD' and x['side'] != 'None'][0]
    except IndexError:
        OPENPOSITION = None
        msg = f'''Current Open Position
{now}

No Open Position
{dict_str(WALLETDICT)}'''

    if OPENPOSITION != None:
        SIZE = OPENPOSITION['size']
        ENTRY = usd_str(OPENPOSITION['entry_price'])
        SIDE = OPENPOSITION['side']

        WALLETDICT.update({'Size': SIZE,
                           'Entry': ENTRY,
                           'Side': SIDE})
        
        STOPORDER = client.Conditional.Conditional_getOrders(stop_order_status='Untriggered').result()[0]['result']['data']
        if len(STOPORDER) == 0:
            STOPPRICE = usd_str(OPENPOSITION['liq_price'])+'***LIQUIDATION PRICE***'
        else:
            if SIDE == 'Buy':
                STOPPRICE = usd_str(max([x['stop_px'] for x in STOPORDER if x['stop_px'] < OPENPOSITION['entry_price'] and x['side'] != SIDE]))
            else:
                STOPPRICE = usd_str(min([x['stop_px'] for x in STOPORDER if x['stop_px'] > OPENPOSITION['entry_price'] and x['side'] != SIDE]))
        
        CLOSEORDER = client.Order.Order_getOrders(order_status='New').result()[0]['result']['data']
        if len(CLOSEORDER) == 0:
            CLOSEPRICE = 'No Close Set'
        else:
            if SIDE == 'Buy':
                CLOSEPRICE = usd_str(min([x['price'] for x in CLOSEORDER if x['price'] > OPENPOSITION['entry_price'] and x['side'] != SIDE]))
            else:
                CLOSEPRICE = usd_str(max([x['price'] for x in CLOSEORDER if x['price'] < OPENPOSITION['entry_price'] and x['side'] != SIDE]))
        
        WALLETDICT.update({'StopPrice': STOPPRICE,
                           'ClosePrice': CLOSEPRICE})
        
        msg = f'''Current Open Position
{now}

{dict_str(WALLETDICT)}'''
    return msg

def cancel_all_orders(account):
    client = load_credentials(account);
    now = datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S')
    stop = len(client.Conditional.Conditional_getOrders(stop_order_status='Untriggered').result()[0]['result']['data'])
    close = len(client.Order.Order_getOrders(order_status='New').result()[0]['result']['data'])
    if stop != 0 or close != 0:
        msg = f'''{now}
        
Canceling all Open Orders
'''
        client.Order.Order_cancelAll(symbol='BTCUSD').result();
    else:
        msg = f'''{now}
        
No Open Orders to Cancel
'''
    return msg

def x1_short(account):
    client = load_credentials(account);
    now = datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S')
    cancel_all_orders(account);
    close_position(account);
    balance = client.Wallet.Wallet_getBalance(coin='BTC').result()[0]['result']['BTC']['equity']
    market_price = float([x['bid_price'] for x in requests.get('https://api.bybit.com/v2/public/tickers?symbol=BTCUSD').json()['result']][0])
    size = int(((market_price + (market_price*0.0015))*balance)*0.995)
    try:
        client.Order.Order_newV2(symbol='BTCUSD', side='Sell', order_type='Market', qty=size, time_in_force='GoodTillCancelled').result();
    except:
        msg = f'''{now}
Failed to Execute Order
Try Again'''
    else:
        msg = 'Short Order Executed'
        msg += current_open(account)
    return msg

def x1_long(account):
    client = load_credentials(account);
    now = datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S')
    cancel_all_orders(account);
    close_position(account);
    balance = client.Wallet.Wallet_getBalance(coin='BTC').result()[0]['result']['BTC']['equity']
    market_price = float([x['ask_price'] for x in requests.get('https://api.bybit.com/v2/public/tickers?symbol=BTCUSD').json()['result']][0])
    size = int(((market_price + (market_price*0.0015))*balance)*0.995)
    try:
        client.Order.Order_newV2(symbol='BTCUSD', side='Buy', order_type='Market', qty=size, time_in_force='GoodTillCancelled').result();
    except:
        msg = f'''{now}
Failed to Execute Order
Try Again'''
    else:
        msg = 'Long Order Executed'
        msg += current_open(account)
    return msg

def close_position(account):
    client = load_credentials(account);
    now = datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S')
    cancel_all_orders(account);
    try:
        OPENPOSITION = [x for x in client.Positions.Positions_myPosition().result()[0]['result'] if x['symbol'] == 'BTCUSD' and x['side'] != 'None'][0]
    except IndexError:
        msg = f'''{now}
        
No Position To Close
'''
    else:
        side = OPENPOSITION['side']
        size = OPENPOSITION['size']
        if side == 'Buy':
            client.Order.Order_newV2(symbol='BTCUSD', side='Sell', order_type='Market', qty=size, time_in_force='GoodTillCancelled').result();
        else:
            client.Order.Order_newV2(symbol='BTCUSD', side='Buy', order_type='Market', qty=size, time_in_force='GoodTillCancelled').result();
        msg = f'''{now}
        
Position Closed
'''
    return msg


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])

def start(update, context):
    """Send a message when the command /choose_account is issued."""
    reply_text = "Welcome to Zalzibab Bybit Trader\n\n"
    if context.user_data:
        reply_text = 'Select "account" to continue'.format(', '.join(context.user_data.keys()))
    else:
        reply_text += 'Select "account" to continue'
    update.message.reply_text(reply_text, reply_markup=markup)
    return CHOOSING

def balance_data(update, context):
    """Send a message when the command /balance is issued."""
    account = context.user_data['account']
    now = datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S')
    msg = f'''Wallet Update
{now}

{dict_str(wallet_update(account))}'''
    update.message.reply_text(msg)

def open_position(update, context):
    """Send a message when the command /open_position is issued."""
    account = context.user_data['account']
    msg = current_open(account)
    update.message.reply_text(msg)
    
def cancel_orders(update, context):
    """Send a message when the command /cancel_orders is issued."""
    account = context.user_data['account']
    msg = cancel_all_orders(account);
    update.message.reply_text(msg)

def short(update, context):
    """Send a message when the command /short is issued."""
    account = context.user_data['account']
    msg = x1_short(account)
    update.message.reply_text(msg)
    
def long(update, context):
    """Send a message when the command /long is issued."""
    account = context.user_data['account']
    msg = x1_long(account)
    update.message.reply_text(msg)
    
def close(update, context):
    """Send a message when the command /close_position is issued."""
    account = context.user_data['account']
    msg = close_position(account);
    update.message.reply_text(msg)


def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    file = 'credentials.pickle'
    exchange = 'Bybit'
    master_credentials = pickle_load(file)
    temp_exchange = {k:v for k,v in master_credentials.items() if k == exchange}
    accounts = dict_str(list_to_dict(list(temp_exchange[exchange].keys())))
    if context.user_data.get(text):
        reply_text = 'Choose an Account on File\n'+accounts.format(text, context.user_data[text])
    else:
        reply_text = 'Choose an Account on File\n'+accounts.format(text)
    update.message.reply_text(reply_text)
    return TYPING_REPLY
    
def received_information(update, context):
    file = 'credentials.pickle'
    exchange = 'Bybit'
    master_credentials = pickle_load(file)
    temp_exchange = {k:v for k,v in master_credentials.items() if k == exchange}
    accounts = dict_str(list_to_dict(list(temp_exchange[exchange].keys())))
    text = update.message.text
    category = context.user_data['choice']
    context.user_data[category] = text
    del context.user_data['choice']

    update.message.reply_text('Saved'.format(facts_to_str(context.user_data)),
                              reply_markup=markup)
    return CHOOSING
    
def done(update, context):
    if 'choice' in context.user_data:
        del context.user_data['choice']
    update.message.reply_text('Account Set'.format(facts_to_str(context.user_data)))
    return ConversationHandler.END
    
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Create the Updater and pass it your bot's token.
    pp = PicklePersistence(filename='Zalzibab Bybit Trader')
    updater = Updater(botAPI, persistence=pp, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('choose_account', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^(account)$'),
                                      regular_choice),
                       ],
            TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_information),
                           ],
        },

        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
        name="Zalzibab Bybit Trader",
        persistent=True
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("balance", balance_data))
    dp.add_handler(CommandHandler("open_position", open_position))
    dp.add_handler(CommandHandler("cancel_orders", cancel_orders))
    dp.add_handler(CommandHandler("short", short))
    dp.add_handler(CommandHandler("long", long))
    dp.add_handler(CommandHandler("close_position", close))
    
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

