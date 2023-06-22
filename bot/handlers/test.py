# Тестовые команды

import statistics
from asyncio import sleep
from pprint import pprint
from time import time
from random import choice

from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           InlineQueryResultContact, Message)

from bot.config import conf, mongo_client
from bot.const import GAME_SETTINGS, ITEMS
from bot.exec import bot
from bot.handlers.dino_profile import transition
from bot.modules.currency import convert
from bot.modules.data_format import seconds_to_str
from bot.modules.donation import check_donations, get_donations
from bot.modules.images import create_egg_image, dino_collecting, dino_game
from bot.modules.inventory_tools import inventory_pages
from bot.modules.item import (AddItemToUser, DowngradeItem, get_data,
                              get_item_dict, get_name)
from bot.modules.localization import get_data, t
from bot.modules.markup import count_markup, down_menu, list_to_keyboard, confirm_markup
from bot.modules.notifications import user_notification, notification_manager
from bot.modules.states_tools import ChoosePagesState, ChooseStepState, prepare_steps
from bot.modules.user import User, max_dino_col
from bot.modules.statistic import get_now_statistic
from bot.modules.quests import create_quest, quest_ui, save_quest
from bot.modules.journey import create_event, random_event

dinosaurs = mongo_client.bot.dinosaurs

async def func(*args):
    print(args)

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    user_id = message.from_user.id
    
    steps = [
        {"type": 'inv', "name": 'item', "data": {}, 
            'message': {'text': 'inventory open'}},
        {"type": 'int', "name": 'str1', "data": {}, 
            'message': {'text': 'hi2', 'reply_markup': list_to_keyboard(['x1', 'x2'])}}
    ]
    
    await ChooseStepState(func, user_id, user_id, 'ru', steps)

@bot.message_handler(commands=['add_item', 'item_add'])
async def command(message):
    user = message.from_user
    if user.id in conf.bot_devs:
        msg_args = message.text.split()

        if len(msg_args) < 4:
            print('-347')

        else:
            ad_user = int(msg_args[1])
            item_id = msg_args[2]
            col = int(msg_args[3])
            
            print('user', ad_user, 'id:', item_id, 'col:', col)
            res = AddItemToUser(ad_user, item_id, col)
            print(res)
    else:
        print(user.id, 'not in devs')


@bot.message_handler(commands=['img_test'])
async def img(message):
    user = User( message.from_user.id)
    
    dino = user.get_last_dino()
    if dino:
        
        for i in range(100):
            img = dino_collecting(dino.data_id, 'all')
            # await bot.send_photo(message.chat.id, img, '13')
        
        print('end')
        

@bot.message_handler(commands=['stress'])
async def stress(message):
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    
    transmitted_data = {
        'userid': user.userid,
        'lang': 'ru'
    }
    
    data = []
    
    for i in range(10):
        print(i)
        try:
            t = time()
            await transition(dino, transmitted_data)
            data.append(time()-t)
        except:
            print('except ', i)
            
    print(statistics.mean(data))
    
    
@bot.message_handler(commands=['egg'])
async def egg(message):
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    
    img = create_egg_image(5, seconds=3000000, lang='ru', rare='leg')
    await bot.send_photo(message.from_user.id, img, '', 
                         )
    
@bot.message_handler(commands=['auto'])
async def test_options_pages(message):
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    if dino:
        await notification_manager(dino._id, 'heal', 50)

@bot.message_handler(commands=['st'])
async def st(message):
    
    get_now_statistic()
    
@bot.message_handler(commands=['eat'])
async def eat(message):
    
    text = ''
    for key, value in ITEMS.items():
        if value['type'] == 'eat':
            text += t(f'items_names.{key}.name', 'ru') + ' ' + value['class'] + '\n'
    
        if value['type'] == 'recipe':
            cr = value['create'][0]['item']
            if ITEMS[cr]['type'] == 'eat':
                text += t(f'items_names.{key}.name', 'ru')
                mat = ''
                for i in value['materials']: 
                    mat += ' ' + i['item'] + ' '
                
                text += mat + '\n'
    
    print(text)
    await bot.send_message(message.chat.id, text)
    
def upd(transmitted_data):
    
    if transmitted_data['return_data']['chose']:
        items = transmitted_data['return_data']['items']
        items_id = []
        
        if type(items) == dict:
            items_id.append(items['item_id'])
        else:
            for i in items: items_id.append(i['item_id'])
        steps = [
            {"type": 'inv', "name": 'items', "data": {
                'exclude_ids': items_id}, 
            'message': {'text': 'inventory open'}},
            {"type": 'bool', "name": 'chose', "data": {}, 
            'message': {'text': 'Добавить ещё предмет?',
                        'reply_markup': list_to_keyboard(['✅ Да', '❌ Нет'])
                        }},
            {'type': 'update_data', 'function': upd,
             'name': 're', 'data': {}}
        ]

        steps = prepare_steps(steps, transmitted_data['userid'], transmitted_data['chatid'], transmitted_data['lang'])

        transmitted_data['steps'] += steps

    return transmitted_data, 0
    
async def ret(return_data, transmitted_data):
    print(return_data)

@bot.message_handler(commands=['inv'])
async def top_inv(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    steps = [
        {"type": 'inv', "name": 'items', "data": {}, 
            'message': {'text': 'inventory open'}},
        {"type": 'bool', "name": 'chose', "data": {}, 
            'message': {'text': 'Добавить ещё предмет?',
                        'reply_markup': list_to_keyboard(['✅ Да', '❌ Нет'])
                        }},
        {
            'type': 'update_data', 'function': upd,
            'name': 're', 'data': {}
        }
    ]

    await ChooseStepState(ret, userid, chatid, lang, steps)

@bot.message_handler(commands=['add_all'])
async def add_all(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    for i in ITEMS:
        AddItemToUser(userid, i, 10)
    
    print('sedf')
    

@bot.message_handler(commands=['journey'])
async def add_all(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    for _ in range(10):
        f = create_event('forest', event='item')
        print(f)
    print('----------------------')

@bot.message_handler(commands=['event'])
async def ev(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    if dino:
        for i in range(10):
            status = await random_event(dino._id, 'forest')
            print(status)

# @bot.message_handler(commands=['names'])
# async def names(message):
    
#     for key in GAME_SETTINGS['collecting_items']:
#         print('\n', key, 'key')
#         for col_key in GAME_SETTINGS['collecting_items'][key]:
#             print('\n', col_key, end=' ')
#             for i in GAME_SETTINGS['collecting_items'][key][col_key]:
                
#                 print(
#                     get_name(i, 'ru'), i
#                 , end=' ')
            
    
#     print('\n43')