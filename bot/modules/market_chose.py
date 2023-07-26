from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str, user_name)
from bot.modules.item import AddItemToUser, counts_items, get_name
from bot.modules.localization import get_data, get_lang, t
from bot.modules.market import (add_product, create_seller,
                                generate_sell_pages, product_ui, seller_ui, generate_items_pages)
from bot.modules.markup import answer_markup, cancel_markup, count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import (ChooseOptionState, ChooseStepState,
                                      prepare_steps)


users = mongo_client.bot.users
management = mongo_client.bot.management
tavern = mongo_client.connections.tavern
sellers = mongo_client.market.sellers
items = mongo_client.bot.items

""" Последняя функция, создаёт продукт и проверяте монеты / предметы
"""
async def end(return_data, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']

    option = transmitted_data['option']
    items = transmitted_data['items']
    col = transmitted_data['col']
    coins = return_data['price']
    in_stock = return_data['in_stock']
    
    if option == 'coins_items': ... # Проверить количество монет 
    elif option in ['items_coins', 'items_items', 'auction']: ... # Проверить предметы

    pr_id = await add_product(userid, option, items, coins, in_stock)
    text, markup = product_ui(lang, pr_id, True)

    await bot.send_message(chatid, text, reply_markup=markup, parse_mode='Markdown')

""" Функция для получения ццены и запаса для типов coins_items / items_coins
"""
async def coins_stock(return_data, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    option = transmitted_data['option']

    if type(return_data['items']) != list:
        return_data['items'] = [return_data['items']]
        return_data['col'] = [return_data['col']]

    steps = [
        {
            "type": 'int', "name": 'price', "data": {"max_int": 10_000_000},
            "translate_message": True,
            'message': {'text': f'add_product.coins.{option}', 
                        'reply_markup': cancel_markup(lang)}
        },
        {
            "type": 'int', "name": 'in_stock', "data": {"max_int": 20},
            "translate_message": True,
            'message': {'text': f'add_product.stock.{option}', 
                        'reply_markup': cancel_markup(lang)}
        }
    ]

    transmitted_data = {
        'items': return_data['items'],
        'col': return_data['col'],
        'option': transmitted_data['option']
    }

    await ChooseStepState(end, userid, chatid, 
                              lang, steps, 
                              transmitted_data=transmitted_data)

""" Функция для получения предметов на обмен (items_items)
"""
async def items_items(return_data, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    option = transmitted_data['option']

    if type(return_data['items']) != list:
        return_data['items'] = [return_data['items']]
        return_data['col'] = [return_data['col']]
    
    print('end', return_data)

""" Функция создаёт проверку на дополнительные предметы, если предметов меньше чем 3
"""
def check_items(transmitted_data):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    option = transmitted_data['option']

    res = True
    circle = new_circle
    if type(transmitted_data['return_data']['items']) == list and len(transmitted_data['return_data']['items']) >= 3: res = False
    if option == 'items_items': circle = trade_circle

    if res:
        not_p_steps = [
            {
                "type": 'bool', "name": 'add_item', "data": {},
                "translate_message": True,
                'message': {'text': 'add_product.add_item',
                             'reply_markup': answer_markup(lang)}
            },
            {
                "type": 'update_data', "name": None, "data": {}, 
                'function': circle
            }
        ]
        steps = prepare_steps(not_p_steps, userid, chatid, lang)
        transmitted_data['steps'] += steps

    return transmitted_data, True

""" Функция выставляет максимальное количетсво предмета для типа coins_items
"""
def update_col(transmitted_data):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    step = transmitted_data['process']

    if type(transmitted_data['return_data']['items']) == list:
        item_data = transmitted_data['return_data']['items'][-1]
    else:
        item_data = transmitted_data['return_data']['items']

    items_res = items.find({'items_data': item_data, "owner_id": userid})
    if items_res:
        max_count = 0
        for i in items_res: max_count += i['count']

        # Добавление данных для выбора количества
        transmitted_data['steps'][step+1]['data']['max_int'] = max_count
        transmitted_data['steps'][step+1]['message']['reply_markup'] = count_markup(max_count, lang)
        transmitted_data['exclude'].append(item_data['item_id'])

        # Очистка лишних данных
        transmitted_data['steps'][step-1] = {}

        return transmitted_data, True
    else: return transmitted_data, False

""" Функция выставляет максимальное количетсво предмета для типа items_coins, items_items.2
    а так же очищает некоторые данные
""" 
def order_update_col(transmitted_data):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    step = transmitted_data['process']

    if type(transmitted_data['return_data']['items']) == list:
        item_data = transmitted_data['return_data']['items'][-1]
    else:
        item_data = transmitted_data['return_data']['items']

    items_res = items.find({'items_data': item_data, "owner_id": userid})
    if items_res:
        max_count = 20

        # Добавление данных для выбора количества
        transmitted_data['steps'][step+1]['data']['max_int'] = max_count
        transmitted_data['steps'][step+1]['message']['reply_markup'] = count_markup(max_count, lang)
        transmitted_data['exclude'].append(item_data['item_id'])

        # Очистка лишних данных
        transmitted_data['steps'][step-1] = {}

        return transmitted_data, True
    else: return transmitted_data, False

""" Создаёт данные для круга получения данных для типа coins_items
"""
def circle_data(userid, chatid, lang, items, option):
    update_function = update_col
    changing_filters = False

    if option == 'coins_items': 
        update_function = order_update_col
        changing_filters = True
    
    not_p_steps = [
        {
            "type": 'inv', "name": 'items', "data": {'inventory': items,
                                                    'changing_filters': changing_filters}, 
            "translate_message": True,
            'message': {'text': f'add_product.chose_item.{option}'}
        },
        {
            "type": 'update_data', "name": None, "data": {}, 
            'function': update_function
        },
        {
            "type": 'int', "name": 'col', "data": {"max_int": 10},
            "translate_message": True,
            'message': {'text': 'css.wait_count', 
                        'reply_markup': None}
        },
        {
            "type": 'update_data', "name": None, "data": {}, 
            'function': check_items
        }
    ]
    steps = prepare_steps(not_p_steps, userid, chatid, lang)
    return steps

""" Создаёт данные для круга получения данных для типа items_items
"""
def trade_circle(userid, chatid, lang, items):

    not_p_steps = [
        {
            "type": 'inv', "name": 'trade_items', "data": {'inventory': items,
                                                    'changing_filters': True}, 
            "translate_message": True,
            'message': {'text': f'add_product.chose_item.items_items'}
        },
        {
            "type": 'update_data', "name": None, "data": {}, 
            'function': order_update_col
        },
        {
            "type": 'int', "name": 'col', "data": {"max_int": 10},
            "translate_message": True,
            'message': {'text': 'css.wait_count', 
                        'reply_markup': None}
        },
        {
            "type": 'update_data', "name": None, "data": {}, 
            'function': check_items
        }
    ]
    steps = prepare_steps(not_p_steps, userid, chatid, lang)
    return steps

""" Функция создаёт ещё 1 круг добавления предмета для типа items_items
"""
def new_trade_circle(transmitted_data):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    add_res = transmitted_data['return_data']['add_item']
    exclude_ids = transmitted_data['exclude']
    
    print('sdfsdf')

    if add_res:
        items, exclude = generate_items_pages(exclude_ids)
        steps = trade_circle(userid, chatid, lang, items)

        transmitted_data['exclude'] = exclude

        transmitted_data['steps'].clear()
        transmitted_data['steps'] = steps
        del transmitted_data['return_data']['add_item']

        transmitted_data['process'] = -1

        return transmitted_data, True
    return transmitted_data, False

""" Функция создаёт ещё 1 круг добавления предмета для типа coins_items
"""
def new_circle(transmitted_data):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    add_res = transmitted_data['return_data']['add_item']
    exclude_ids = transmitted_data['exclude']
    option = transmitted_data['option']

    if add_res:
        items, exclude = generate_sell_pages(userid, exclude_ids)
        steps = circle_data(userid, chatid, lang, items, option)

        transmitted_data['exclude'] = exclude

        transmitted_data['steps'].clear()
        transmitted_data['steps'] = steps
        del transmitted_data['return_data']['add_item']

        transmitted_data['process'] = -1

        return transmitted_data, True
    return transmitted_data, False

""" Старт всех проверок
"""
async def prepare_data_option(option, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    steps = []
    ret_function = coins_stock

    if option in ['items_coins', 'coins_items']:
        if option == 'items_coins':
            items, exclude = generate_sell_pages(userid)
        else:
            items, exclude = generate_items_pages()

        steps = circle_data(userid, chatid, lang, items, option)
        transmitted_data = {
            'exclude': exclude, 'option': option
        }

    elif option == 'items_items':
        ret_function = items_items
        items, exclude = generate_sell_pages(userid)
        steps = circle_data(userid, chatid, lang, items, option)
        transmitted_data = {
            'exclude': exclude, 'option': option
        }

    await ChooseStepState(ret_function, userid, chatid, 
                            lang, steps, 
                            transmitted_data=transmitted_data)