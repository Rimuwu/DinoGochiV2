# Тестовые команды

from telebot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultContact
from bot.exec import bot
from bot.modules.item import get_name, get_item_dict, get_data, AddItemToUser, DowngradeItem
from bot.config import mongo_client, conf
from bot.modules.user import User, max_dino_col
from bot.modules.donation import check_donations, get_donations
from time import time
from pprint import pprint
from bot.modules.currency import convert
from bot.modules.notifications import user_notification
from bot.modules.inventory_tools import inventory_pages
from bot.modules.markup import list_to_keyboard, count_markup
from asyncio import sleep
from bot.const import ITEMS
from bot.modules.states_tools import ChooseStepState
from bot.modules.data_format import seconds_to_str 
from bot.modules.images import dino_game

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


# @bot.message_handler(commands=['img_test'])
# async def img(message):
#     user = User( message.from_user.id)
    
#     dino = user.get_last_dino()
#     if dino:
#         img = dino_game(dino.data_id, dino.age.days)
#         await bot.send_photo(message.chat.id, img, '13')