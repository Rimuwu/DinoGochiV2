# Тестовые команды

from asyncio import sleep
from pprint import pprint
from time import time

from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           InlineQueryResultContact, Message)

from bot.config import conf, mongo_client
from bot.const import ITEMS, GAME_SETTINGS
from bot.exec import bot
from bot.modules.currency import convert
from bot.modules.data_format import seconds_to_str
from bot.modules.donation import check_donations, get_donations
from bot.modules.images import dino_game, dino_collecting
from bot.modules.inventory_tools import inventory_pages
from bot.modules.item import (AddItemToUser, DowngradeItem, get_data,
                              get_item_dict, get_name)
from bot.modules.markup import count_markup, list_to_keyboard
from bot.modules.notifications import user_notification
from bot.modules.states_tools import ChooseStepState
from bot.modules.user import User, max_dino_col

from bot.handlers.dino_profile import transition

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
    
    for i in range(100):
        print(i)
        try:
            await transition(dino, transmitted_data)
        except:
            print('except ', i)
    
    
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