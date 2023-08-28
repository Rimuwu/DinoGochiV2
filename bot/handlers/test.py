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
from bot.modules.data_format import seconds_to_str, str_to_seconds
from bot.modules.donation import check_donations, get_donations
from bot.modules.images import create_egg_image, dino_collecting, dino_game
from bot.modules.inventory_tools import inventory_pages
from bot.modules.item import (AddItemToUser, DowngradeItem, get_data,
                              get_item_dict, get_name)
from bot.modules.localization import get_data, t
from bot.modules.markup import count_markup, down_menu, list_to_keyboard, confirm_markup
from bot.modules.notifications import user_notification, notification_manager
from bot.modules.states_tools import ChoosePagesState, ChooseStepState, prepare_steps
from bot.modules.user import User, max_dino_col, award_premium
from bot.modules.statistic import get_now_statistic
from bot.modules.quests import create_quest, quest_ui, save_quest
from bot.modules.journey import create_event, random_event, activate_event

from bot.modules.market import (add_product, create_seller,
                                generate_sell_pages, product_ui, seller_ui)

dinosaurs = mongo_client.dinosaur.dinosaurs
products = mongo_client.market.products
sellers = mongo_client.market.sellers
puhs = mongo_client.market.puhs
items = mongo_client.item.items

async def func(*args):
    print(args)

@bot.message_handler(commands=['test'], is_admin=True)
async def test_command(message: Message):
    user_id = message.from_user.id
    
    steps = [
        {"type": 'inv', "name": 'item', "data": {}, 
            'message': {'text': 'inventory open'}},
        {"type": 'int', "name": 'str1', "data": {}, 
            'message': {'text': 'hi2', 'reply_markup': list_to_keyboard(['x1', 'x2'])}}
    ]
    
    await ChooseStepState(func, user_id, user_id, 'ru', steps)

@bot.message_handler(commands=['add_item', 'item_add'], is_admin=True)
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


@bot.message_handler(commands=['img_test'], is_admin=True)
async def img(message):
    user = User( message.from_user.id)
    
    dino = user.get_last_dino()
    if dino:
        
        for i in range(100):
            img = dino_collecting(dino.data_id, 'all')
            # await bot.send_photo(message.chat.id, img, '13')
        
        print('end')
        

@bot.message_handler(commands=['stress'], is_admin=True)
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
    
    
@bot.message_handler(commands=['egg'], is_admin=True)
async def egg(message):
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    
    img = create_egg_image(5, seconds=3000000, lang='ru', rare='leg')
    await bot.send_photo(message.from_user.id, img, '', 
                         )
    
@bot.message_handler(commands=['auto'], is_admin=True)
async def test_options_pages(message):
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code

    user = User( message.from_user.id)
    dino = user.get_last_dino()
    if dino: await notification_manager(dino._id, 'heal', 50)

@bot.message_handler(commands=['st'], is_admin=True)
async def st(message):
    
    get_now_statistic()
    
@bot.message_handler(commands=['eat'], is_admin=True)
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

@bot.message_handler(commands=['inv'], is_admin=True)
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

@bot.message_handler(commands=['add_all'], is_admin=True)
async def add_all(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    for i in ITEMS:
        AddItemToUser(userid, i, 10)
    
    print('add_all items')
    

@bot.message_handler(commands=['journey'], is_admin=True)
async def add_all(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    
    for _ in range(10):
        event = create_event('lost-islands', event='battle')
        await activate_event(dino._id, event)
        # print(f)
    print('----------------------')

@bot.message_handler(commands=['event'], is_admin=True)
async def ev(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code

    user = User( message.from_user.id)
    dino = user.get_last_dino()
    if dino:
        for i in range(5):
            event = create_event('forest', 'positive', 0, 'influences_mood')
            await activate_event(dino._id, event)
        for i in range(5):
            event = create_event('forest', 'negative', 0, 'influences_mood')
            await activate_event(dino._id, event)



@bot.message_handler(commands=['all_events'], is_admin=True)
async def ev(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    
    positive = {
            'com': ['influences_mood', 'without_influence', 
                  'influences_eat', 'influences_game'],
            'unc': ['influences_health', 'influences_energy',
                   'joint_activity'],
            'rar': ['coins', 'joint_event', 'meeting_friend'],
            'mys': ['trade_item', 'item'],
            'leg': ['quest', 'coins']
        }
    negative = {
        'com': ['influences_mood', 'without_influence', 
                'influences_eat'],
        'unc': ['influences_energy', 'coins'],
        'rar': ['influences_game', 'coins'],
        'mys': ['item', 'coins'],
        'leg': ['quest', 'edit_location']
    }
    
    if dino:
        for key in positive:
            for eve in positive[key]:
                event = create_event('forest', 'positive', 0, eve)
                await activate_event(dino._id, event)
            # status = await random_event(dino._id, 'forest')
            # print(status)
    
    if dino:
        for key in negative:
            for eve in negative[key]:
                event = create_event('forest', 'negative', 0, eve)
                await activate_event(dino._id, event)

    # for eve in ['battle']:
    #     event = create_event('lost-islands', 'positive', 0, eve)
    #     await activate_event(dino._id, event)
    
    # for i in range(10):
    #     for eve in ['battle']:
    #         event = create_event('lost-islands', 'negative', 0, eve)
    #         await activate_event(dino._id, event)

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

@bot.message_handler(commands=['qqq'], is_admin=True)
async def add_all(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    user = User( message.from_user.id)
    dino = user.get_last_dino()
    
    quest = create_quest(1, 'journey', lang=lang)
    save_quest(quest, userid)



@bot.message_handler(commands=['product'], is_admin=True)
async def product(message):
    
    userid = message.from_user.id
    chatid = message.chat.id
    
    product = products.find_one({'alt_id': '1191252229_m1Sgp0GN'})
    text, markup = product_ui('ru', product['_id'], False)
    
    await bot.send_message(chatid, text, 
                           reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['ttt'], is_admin=True)
async def ttt(message):

    userid = message.from_user.id
    chatid = message.chat.id

    text = seconds_to_str(1000, 'ru', False, 'hour')
    print(text)

@bot.message_handler(commands=['give_me_premium'], is_admin=True)
async def give_me_premium(message):
    
    userid = message.from_user.id
    award_premium(userid, 'inf')
    print('add premium')

@bot.message_handler(commands=['dbtest'], is_admin=True)
async def dbtest(message):
    
    st = time()
    col = items.count_documents({})
    print(time() - st)
    print(col)

    st = time()
    itm = items.find({})[1000]
    print(time() - st)
    print(itm)

@bot.message_handler(commands=['create_test'], is_admin=True)
async def create_test(message):
    id_l = list(ITEMS.keys())

    all_t = time()
    for i in range(600_000):
        st = time()
        status = AddItemToUser(i, choice(id_l), 1)
        print(time() - st)

        print(i)
    print('alll ', time() - all_t)


@bot.message_handler(commands=['time'], is_admin=True)
async def time_t(message):

    txt = message.text.replace('/time ', '')
    print(str_to_seconds(txt))