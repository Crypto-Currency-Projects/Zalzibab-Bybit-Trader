#!/usr/bin/env python
# coding: utf-8

import pickle
import os
from datetime import datetime
from bybit import bybit
import warnings
warnings.simplefilter("ignore")
import requests


def list_to_dict(list_item):
    temp = {}
    for x,y in enumerate(list_item):
        temp[x+1] = y
    return temp

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

def pickle_write(file, item):
    with open(file, 'wb') as handle:
        pickle.dump(item, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return print(file+' saved')

def pickle_load(file):
    with open(file, 'rb') as handle:
        temp = pickle.load(handle)
    return temp

def dict_str(dict_item):
    dict_msg = ''
    try:
        for x in range(len(dict_item)):
            for k, v in dict_item[x].items():
                dict_msg += k+': '+str(v)+'\n'
            dict_msg += '\n'
    except KeyError:
        for k, v in dict_item.items():
            dict_msg += k+': '+str(v)+'\n'
    return dict_msg

#Telegram Text Alert
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


def load_exchange(exchange):
    file = 'credentials.pickle'
    load_connection = False
    create_connection = False
    confirm_connection = False
    if os.path.exists(file):
        try:
            master_credentials = pickle_load(file)[exchange]
        except KeyError:
            account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
            master_credentials = pickle_load(file)
            master_credentials[exchange] = {account_name: {'api_key': None,
                                                           'api_secret': None}}
            create_connection = True
        else:
            master_credentials = pickle_load(file)
            load_connection = True
    else:
        account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
        master_credentials = {exchange: {account_name: {'api_key': None,
                                                        'api_secret': None}}}
        create_connection = True
    if load_connection:
        while True:
            account_names = list(master_credentials[exchange].keys())
            account_name = list_prompt('Choose your saved '+exchange+' account', account_names+['New '+exchange+' Account'])
            if account_name == 'New '+exchange+' Account':
                account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
                create_connection = True
                break
            else:
                existing_options = ['Load', 'Edit', 'Delete']
                existing_selection = list_prompt('Choose action for '+account_name, existing_options)
                if existing_selection == 'Load':
                    credentials = master_credentials[exchange][account_name]
                    confirm_connection = True
                    break
                elif existing_selection == 'Edit':
                    create_connection = True
                    break
                elif existing_selection == 'Delete':
                    del master_credentials[exchange][account_name]
                    continue
    if confirm_connection:
        print('Confirm '+exchange+' Connection')
        resp = y_n_prompt()
        if resp == 'No':
            print('Create New '+exchange+' Credentials')
            account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
            create_connection = True
    if create_connection:
        while True:
            api_key = str(input('Input Your '+exchange+' API Key'+'\n'+'> '))
            api_secret = str(input('Input Your '+exchange+' API Secret'+'\n'+'> '))
            credentials = {exchange: {account_name: {'api_key': api_key,
                                                     'api_secret': api_secret}}}
            if exchange == 'Bitmex':
                client = bitmex(test=False,api_key=api_key,
                                api_secret=api_secret);
                try:
                    print('\n'+'Testing '+exchange+' Credentials'+'\n')
                    client.User.User_getWalletHistory().result();
                except bravado.exception.HTTPError:
                    print('Invalid '+exchange+' Credentials'+'\n')
                    continue
                else:
                    print(exchange+' Credentials Verified'+'\n')
                    break
            elif exchange == 'Bybit':
                client = bybit(test=False,api_key=api_key,
                               api_secret=api_secret)
                resp = client.APIkey.APIkey_info().result()[0]['ret_msg'];
                if resp == 'invalid api_key':
                    print('Invalid '+exchange+' Credentials'+'\n')
                    continue
                else:
                    print(exchange+' Credentials Verified'+'\n')
                    break
            elif exchange == 'qTrade':
                client = QtradeAPI('https://api.qtrade.io', key=api_key)
                try:
                    client.get("/v1/user/me")
                except (APIException, requests.exceptions.ConnectionError, ConnectionResetError):
                    print('Invalid Credentials'+'\n')
                    continue
                else:
                    print('qTrade Credentials Verified'+'\n')
                    break  
    
        master_credentials[exchange].update(credentials[exchange])
        pickle_write(file, master_credentials)
    return master_credentials[exchange][account_name]


while True:
    file = 'credentials.pickle'
    exchanges = ['Bybit', 'Exit']
    exchange = list_prompt('Choose an Exchange', exchanges)
    
    if exchange == 'Exit':
        break
        
    if os.path.exists(file) == False:
        load_exchange(exchange)
        load_bot()
    try:
        pickle_load(file)[exchange]
    except KeyError:
        print('No '+exchange+' Credentials on File')
        continue
    master_credentials = pickle_load(file)
    
    temp_exchange = {k:v for k,v in master_credentials.items() if k == exchange}
    accounts = list(temp_exchange[exchange].keys())+['New Account/Edit Existing']
    account = list_prompt('Choose an '+exchange+' Account', accounts)
    if account == accounts[-1]:
        load_exchange(exchange)
        continue
    temp_exchange = {k:v for k,v in temp_exchange[exchange].items() if k == account}
    print('Use '+exchange+' Bot?')
    resp = y_n_prompt()
    if resp == 'Yes':
        temp_bot = {k:v for k,v in master_credentials.items() if k == 'bots'}
        bot_accounts = list(temp_bot['bots'].keys())
        bot_account = list_prompt('Choose a Telegram Bot', bot_accounts+['New Bot'])
        if bot_account == 'New Bot':
            load_bot()
            continue
        temp_bot = {k:v for k,v in temp_bot['bots'].items() if k == bot_account}

