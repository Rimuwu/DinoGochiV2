from telebot.asyncio_handler_backends import State, StatesGroup

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.inventory_tools import start_inv
from bot.modules.item import get_data, get_name, use_item
from bot.modules.localization import t
from bot.modules.markup import (confirm_markup, count_markup,
                                get_answer_keyboard)
from bot.modules.markup import markups_menu as m
from bot.modules.user import User

items = mongo_client.bot.items

class GeneralStates(StatesGroup):
    ChooseDino = State() # Состояние для выбора динозавра
    ChooseInt = State() # Состояние для ввода числа
    ChooseString = State() # Состояние для ввода текста
    ChooseConfirm = State() # Состояние для подтверждения (да / нет)
    ChooseOption = State() # Состояние для выбора среди вариантов

def add_if_not(data: dict, userid: int, chatid: int, lang: str):
    """Добавляет минимальные данные для работы"""
    if 'userid' not in data: data['userid'] = userid
    if 'chatid' not in data: data['chatid'] = chatid
    if 'lang' not in data: data['lang'] = lang
    return data

async def ChooseDinoState(function, userid: int, chatid: int, 
        lang: str, add_egg: bool=True, 
        transmitted_data: dict | None=None):
    """ Устанавливает состояние ожидания динозавра

       В function передаёт 
       >>> element: Dino | Egg, transmitted_data: dict
       
       Return:
        Возвращает 2 если был создано состояние, 1 если завершилось автоматически (1 вариант выбора), 0 - невозможно завершить
    """
    user = User(userid)
    elements = user.get_dinos
    if add_egg: elements += user.get_eggs
    if not transmitted_data: transmitted_data = {}
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    ret_data = get_answer_keyboard(elements, lang)

    if ret_data['case'] == 0:
        await bot.send_message(userid, 
            t('p_profile.no_dinos_eggs', lang),
            reply_markup=m(userid, 'last_menu', lang))
        return False, 'cancel'

    elif ret_data['case'] == 1: #1 динозавр / яйцо, передаём инфу в функцию
        element = ret_data['element']
        await function(element, transmitted_data)
        return False, 'dino'

    elif ret_data['case'] == 2:# Несколько динозавров / яиц
        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, GeneralStates.ChooseDino, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['dino_names'] = ret_data['data_names']
            data['transmitted_data'] = transmitted_data

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=ret_data['keyboard'])
        return True, 'dino'

async def ChooseIntState(function, userid: int, 
                chatid: int, lang: str,
                min_int: int = 1, max_int: int = 10,
                transmitted_data: dict | None=None):
    """ Устанавливает состояние ожидания числа

        В function передаёт 
        >>> number: int, transmitted_data: dict
        
        Return:
         Возвращает True если был создано состояние, False если завершилось автоматически (минимальный и максимальный вариант совпадают)
    """
    
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    
    if min_int != max_int:
        await bot.set_state(userid, GeneralStates.ChooseInt, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['transmitted_data'] = transmitted_data
            data['min_int'] = min_int
            data['max_int'] = max_int
        return True, 'int'
    else:
        await function(min_int, transmitted_data)
        return False, 'int'

async def ChooseStringState(function, userid: int, 
                         chatid: int, lang: str,
                         min_len: int = 1, max_len: int = 10,
                         transmitted_data: dict | None=None):
    """ Устанавливает состояние ожидания сообщения

        В function передаёт 
        >>> string: str, transmitted_data: dict
        
        Return:
         Возвращает True если был создано состояние, не может завершится автоматически
    """
    if not transmitted_data: transmitted_data = {}
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseString, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
        data['min_len'] = min_len
        data['max_len'] = max_len
    return True, 'string'

async def ChooseConfirmState(function, userid: int, 
                         chatid: int, lang: str, cancel: bool=False,
                         transmitted_data: dict | None=None):
    """ Устанавливает состояние ожидания подтверждения действия

        В function передаёт 
        >>> answer: bool, transmitted_data: dict
        
        Return:
         Возвращает True если был создано состояние, не может завершится автоматически
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data['cancel'] = cancel
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseConfirm, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
    return True, 'confirm'

async def ChooseOptionState(function, userid: int, 
                         chatid: int, lang: str,
                         options: dict = {},
                         transmitted_data: dict | None=None):
    """ Устанавливает состояние ожидания выбора опции

        В function передаёт 
        >>> answer: ???, transmitted_data: dict
        
        Return:
         Возвращает True если был создано состояние, False если завершилось автоматически (1 вариант выбора)
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    
    if len(options) > 1:
        await bot.set_state(userid, GeneralStates.ChooseOption, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['transmitted_data'] = transmitted_data
            data['options'] = options
        return True, 'option'
    else:
        element = options[list(options.keys())[0]]
        await function(element, transmitted_data)
        return False, 'option'

async def ChooseStepState(function, userid: int, 
                         chatid: int, lang: str,
                         steps: list = [],
                         transmitted_data: dict | None=None):
    """ Конвеерная Система Состояний
        Устанавливает ожидание нескольких ответов, запуская состояния по очереди.
        
        steps = [
            {"type": str, "name": str, "data": dict, 
                'message': {'text': str, 'reply_markup': markup}}
        ]
        type - тип опроса пользователя (chooses)
        name - имя ключа в возвращаемом инвентаре (не повторять для корректности)
        data - данные для функции создания опроса
        message - данные для отправляемо сообщения перед опросом

        В function передаёт 
        >>> answer: dict, transmitted_data: dict
    """
    if not transmitted_data: transmitted_data = {}
    
    chooses = {
        'dino': ChooseDinoState,
        'int': ChooseIntState,
        'str': ChooseStringState,
        'bool': ChooseConfirmState,
        'option': ChooseOptionState,
        'inv': start_inv
    }
    for step in steps:
        if step['type'] in chooses:
            step['function'] = chooses[step['type']]
            
            step['data'] = dict(add_if_not(
                step['data'], userid, chatid, lang))
        else:
            steps.remove(step)
    
    transmitted_data = dict(add_if_not(transmitted_data, 
                            userid, chatid, lang))
    
    transmitted_data['steps'] = steps
    transmitted_data['return_function'] = function
    transmitted_data['return_data'] = {}
    await next_step(0, transmitted_data, True)


# Должен быть ниже всех других обработчиков, 
# для возможности их использования
async def next_step(answer, transmitted_data: dict, start: bool=False):
    """Обработчик КСС*

    Args:
        answer (_type_): Ответ переданный из функции ожидания
        transmitted_data (dict): Переданная дата
        start (bool, optional): Является ли функция стартом КСС Defaults to False.
    """
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    
    steps = transmitted_data['steps']
    return_data = transmitted_data['return_data']

    # Обновление внутренних данных
    if not start:
        name = steps[len(return_data)]['name']
        if name:
            transmitted_data['return_data'][name] = answer

    if len(return_data) != len(steps): #Получение данных по очереди
        ret_data = steps[len(return_data)]

        # Следующая функция по счёту
        func_answer, func_type = await ret_data['function'](next_step, 
                    transmitted_data=transmitted_data, **ret_data['data']
        )
        if func_type == 'inv':
            print('============================================')
            print(ret_data['data'])
        
        # Отправка если состояние было добавлено и не была завершена автоматически
        if func_type == 'cancel':
            # Если функция возвращает не свой тип, а "cancel" - её надо принудительно завершить
            await bot.delete_state(userid, chatid)
            await bot.reset_data(userid, chatid)
        if func_answer:
            # Отправка сообщения из message: dict, если None - ничего
            if ret_data['message']:
                await bot.send_message(userid, **ret_data['message'])
        # Обновление данных состояния
        if not start:
            async with bot.retrieve_data(userid, chatid) as data:
                data['transmitted_data'] = transmitted_data

    else: #Все данные получены
        await bot.delete_state(userid, chatid)
        await bot.reset_data(userid, chatid)

        return_function = transmitted_data['return_function']
        del transmitted_data['steps']
        del transmitted_data['return_function']
        del transmitted_data['return_data']

        await return_function(return_data, transmitted_data)

async def adapter(return_data: dict, transmitted_data: dict):
    del return_data['confirm']
    
    use_item(transmitted_data['userid'], transmitted_data['chatid'], 
             transmitted_data['items_data'], **return_data)

async def data_for_use_item(item: dict, userid: int, chatid: int, lang: str):
    item_id: str = item['item_id']
    data_item: dict = get_data(item_id)
    type_item: str = data_item['type']
    item_name = get_name(item_id, lang)
    steps = []
    transmitted_data = {'items_data': item}
    
    base_item = items.find_one({'owner_id': userid, 'items_data': item})

    if type(base_item) is None:
        await bot.send_message(chatid, t('item_use.no_item', lang))
    elif type(base_item) is dict:
        max_count = base_item['count']
        
        if type_item == 'eat':
            steps = [
                {"type": 'dino', "name": 'dino', "data": {"add_egg": False}, 
                    'message': None},
                {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                    'message': {'text': t('css.wait_count', lang), 
                                'reply_markup': count_markup(max_count)}}
            ]
        elif type_item in ['game_ac', 'sleep_ac', 
                           'journey_ac', 'collecting_ac', 
                           'weapon', 'backpack', 'armor']:
            steps = [
                {"type": 'dino', "name": 'dino', "data": {"add_egg": False}, 
                    'message': None}
            ]
        elif type_item == 'recipe':
            max_count = base_item['count'] * item['abilities']['uses']
            steps = [
                {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                    'message': {'text': t('css.wait_count', lang), 
                                'reply_markup': count_markup(max_count)}}
            ]
        elif type_item == 'weapon':
            steps = [
                {"type": 'dino', "name": 'dino', "data": {"add_egg": False}, 
                    'message': None}
            ]
        elif type_item == 'ammunition':
            steps = [
                {"type": 'inv', "name": 'combine_item', "data": {
                    'item_filter': [item_id],
                    'changing_filters': False
                        }, 
                    'message': {'text': t('css.combine', lang, 
                                          name=item_name)}}
            ]
        elif type_item == 'case':
            steps = [
                {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                    'message': {'text': t('css.wait_count', lang), 
                                'reply_markup': count_markup(max_count)}}
            ]
        steps.insert(0, {"type": 'bool', "name": 'confirm', 
                         "data": {'cancel': True}, 'message': 
                             {
                                'text': t('css.confirm', lang, name=item_name),
                                'reply_markup': confirm_markup(lang)
                             }
                        }
                     )
        await ChooseStepState(adapter, userid, chatid, lang, steps, 
                              transmitted_data=transmitted_data)

async def back_to_state():
    """ Функция возвращает к прошлому состоянию. 
    
        То есть по идеи мы после ChooseStepState вызываем эту функцию и говорим что хотим вернутся к инвентарю, он проверяет это и возвращает обратно.
    """
    ...