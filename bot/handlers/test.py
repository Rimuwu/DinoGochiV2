# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.item import get_name, get_item_dict, get_data, AddItemToUser
from bot.config import mongo_client
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



@bot.message_handler(commands=['add_8'])
async def add(message: Message):
    user_id = message.from_user.id
    
    m, res = AddItemToUser(user_id, "8", 20)
    print(m, res)
