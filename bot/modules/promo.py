from telebot.types import Message, InputMedia

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str, user_name, escape_markdown)
from bot.modules.item import (AddItemToUser, CheckCountItemFromUser,
                              RemoveItemFromUser, counts_items, get_name)
from bot.modules.localization import get_data, get_lang, t
from bot.modules.market import (add_product, preview_product,
                                generate_items_pages, generate_sell_pages,
                                product_ui, seller_ui, delete_product, buy_product, create_preferential, check_preferential)
from bot.modules.markup import answer_markup, cancel_markup, count_markup, confirm_markup
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import (ChooseIntState, ChooseStringState,
                                      ChooseStepState, prepare_steps, ChooseConfirmState, ChoosePagesState)
from bot.modules.markup import markups_menu as m
from bot.modules.user import take_coins
from random import choice
from bot.modules.market import generate_items_pages

users = mongo_client.user.users
management = mongo_client.other.management
tavern = mongo_client.tavern.tavern
sellers = mongo_client.market.sellers
products = mongo_client.market.products


async def create_promo_start(userid: int, chatid: int, lang: str):

    steps = [
        {
            "type": 'str', "name": 'code', "data": {"max_len": 0, "min_len": 1},
            "translate_message": True,
            'message': {'text': 'promo.code', 
                        'reply_markup': cancel_markup(lang)}
        },
        {
            "type": 'int', "name": 'coins', "data": {"max_int": 100_000, 'min_int': 0},
            "translate_message": True,
            'message': {'text': 'promo.coins', 
                        'reply_markup': cancel_markup(lang)}
        },
        {
            "type": 'int', "name": 'count', "data": {"max_int": 1_000_000, 'min_int': 0},
            "translate_message": True,
            'message': {'text': 'promo.count', 
                        'reply_markup': cancel_markup(lang)}
        },
        {
            "type": 'time', "name": 'time_end', "data": {"max_int": 0, "min_int": 0},
            "translate_message": True,
            'message': {'text': 'promo.time_end', 
                        'reply_markup': cancel_markup(lang)}
        }
    ]

    await ChooseStepState(start_items, userid, chatid, lang, steps)

async def start_items(return_data, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    
    code = return_data['code']
    coins = return_data['coins']
    count = return_data['count']
    time_end = return_data['time_end']

    items, exclude = generate_items_pages(ignore_cant=True)
    steps = circle_data(userid, chatid, lang, items)
    await ChooseStepState(end, userid, chatid, lang, steps,
                          transmitted_data={'code': code, 'coins': coins,
                                            'count': count, 'time_end': time_end}
                          )

""" Создаёт данные для круга получения данных для типа coins_items
"""
def circle_data(userid, chatid, lang, items, prepare: bool = True):
    not_p_steps = [
        {
            "type": 'inv', "name": 'items', "data": {'inventory': items}, 
            "translate_message": True,
            'message': {'text': f'promo.chose_item'}
        },
        {
            "type": 'update_data', "name": None, "data": {}, 
            'function': update_col
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
    if prepare:
        steps = prepare_steps(not_p_steps, userid, chatid, lang)
        return steps
    else: return not_p_steps

""" Функция выставляет максимальное количетсво предмета
"""
def update_col(transmitted_data):
    lang = transmitted_data['lang']
    step = transmitted_data['process']

    if type(transmitted_data['return_data']['items']) == list:
        item_data = transmitted_data['return_data']['items'][-1]
    else:
        item_data = transmitted_data['return_data']['items']

    # Добавление данных для выбора количества
    transmitted_data['steps'][step+1]['data']['max_int'] = 1000
    transmitted_data['steps'][step+1]['message']['reply_markup'] = count_markup(100, lang)
    if 'exclude' not in transmitted_data: 
        transmitted_data['exclude'] = []
    transmitted_data['exclude'].append(item_data['item_id'])

    # Очистка лишних данных
    transmitted_data['steps'][step-1] = {}

    return transmitted_data, True

def check_items(transmitted_data):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']

    not_p_steps = [
        {
            "type": 'bool', "name": 'add_item', "data": {},
            "translate_message": True,
            'message': {'text': 'add_product.add_item',
                            'reply_markup': answer_markup(lang)}
        },
        {
            "type": 'update_data', "name": None, "data": {}, 
            'function': new_circle
        }
    ]
    steps = prepare_steps(not_p_steps, userid, chatid, lang)
    transmitted_data['steps'] += steps

    return transmitted_data, True

""" Функция создаёт ещё 1 круг добавления предмета для типа
"""
def new_circle(transmitted_data):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    add_res = transmitted_data['return_data']['add_item']
    exclude_ids = transmitted_data['exclude']

    if add_res:
        items, exclude = generate_items_pages(exclude_ids, ignore_cant=True)
        steps = circle_data(userid, chatid, lang, items)

        transmitted_data['exclude'] = exclude

        transmitted_data['steps'].clear()
        transmitted_data['steps'] = steps
        del transmitted_data['return_data']['add_item']

        transmitted_data['process'] = -1

        return transmitted_data, True
    return transmitted_data, False

async def end(return_data, transmitted_data):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    print(return_data)