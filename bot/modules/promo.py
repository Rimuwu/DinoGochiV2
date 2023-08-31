from telebot.types import Message, InputMedia

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str, user_name, escape_markdown)
from bot.modules.item import (AddItemToUser, CheckCountItemFromUser,
                              RemoveItemFromUser, counts_items, get_name, items)
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
from time import time

promo = mongo_client.other.promo
users = mongo_client.user.users

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

    code = transmitted_data['code']
    coins = transmitted_data['coins']
    count = transmitted_data['count']
    time_end = transmitted_data['time_end']

    if type(return_data['items']) != list:
        add_items = [return_data['items']] * return_data['col']
    else:     
        add_items, a = [], 0
        for item in return_data['items']:
            add_items += [item] * return_data['col'][a]
            a += 1

    if time_end == 0: time_end = 'inf'
    if count == 0: count = 'inf'

    create_promo(code, count, time_end, coins, add_items)

    text, markup = promo_ui(code, lang)
    try:
        await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)
    except:
        await bot.send_message(chatid, text, reply_markup=markup)
    await bot.send_message(chatid, '✅', reply_markup=m(userid, 'last_menu', lang))

def create_promo(code: str, col, seconds, coins: int, items: list):
    data = {
        "code": code,
        "users": [],
        "col": col,
        "time_end": seconds,
        "time": seconds,
        "coins": coins,
        "items": items,
        "active": False
    }

    promo.insert_one(data)

def promo_ui(code: str, lang: str):
    data = promo.find_one({"code": code})
    text, markup = '', None

    if data:
        status = ''
        if data['active']: status = '✅'
        else: status = '❌'

        id_list = []
        for i in data['items']: id_list.append(i['item_id'])

        if data['time_end'] == 'inf':
            txt_time = '♾'
        else: txt_time = seconds_to_str(data['time_end'] - int(time()), lang)

        text = t('promo_commands.ui.text', lang,
                 code=code, status=status,
                 col=data['col'], coins=data['coins'],
                 items=counts_items(id_list, lang),
                 txt_time=txt_time)

        but = get_data('promo_commands.ui.buttons', lang)
        inl_l = {
            but[0]: f'promo {code} activ',
            but[1]: f'promo {code} delete',
            but[2]: f'promo {code} use'
        }

        markup = list_to_inline([inl_l], 2)
    return text, markup

def get_promo_pages() -> dict:
    res = list(promo.find({}))
    data = {}
    if res: 
        for i in res: data[i['code']] = i['code']
    return data

def use_promo(code: str, userid: int, lang: str):
    data = promo.find_one({"code": code})
    user = users.find_one({'userid': userid}, {'userid': 1})
    text = ''

    if user:
        if data:
            col = data['col']
            if col == 'inf': col = 1

            seconds = data['time_end']
            if seconds == 'inf': seconds = int(time()) + 100

            if data['active']:
                if col:
                    if seconds - int(time()) > 0:
                        if userid not in data['users']:

                            promo.update_one({'_id': data['_id']},
                                             {"$push": {f'users': userid}
                                              })

                            if data['col'] != 'inf':
                                promo.update_one({'_id': data['_id']},
                                                 {"$inc": {f'col': -1}})

                            text = t('promo_commands.activate', lang)
                            if data['coins']:
                                text += t('promo_commands.coins', lang,
                                          coins=data['coins']
                                          )
                            if data['items']:
                                id_list = []
                                for i in data['items']: id_list.append(i['item_id'])
                                text += t('promo_commands.items', lang,
                                          items=counts_items(id_list, lang)
                                          )
                            return 'ok', text
                        else:
                            text = t('promo_commands.already_use', lang)
                            return 'already_use', text
                    else:
                        text = t('promo_commands.time_end', lang)
                        return 'time_end', text
                else:
                    text = t('promo_commands.max_col', lang)
                    return 'max_col_use', text
            else:
                text = t('promo_commands.deactivated', lang)
                return 'deactivated', text
        else:
            text = t('promo_commands.not_found', lang)
            return 'not_found', text
    text = t('promo_commands.no_user', lang)
    return 'no_user', text