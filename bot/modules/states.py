from telebot.asyncio_handler_backends import State, StatesGroup

from bot.exec import bot
from bot.modules.localization import t
from bot.modules.markup import get_answer_keyboard
from bot.modules.user import User


class GeneralStates(StatesGroup):
    ChooseDino = State() # Состояние для выбора динозавра
    ChooseInt = State() # Состояние для ввода числа
    ChooseString = State() # Состояние для ввода текста
    ChooseConfirm = State() # Состояние для подтверждения (да / нет)
    ChooseOption = State() # Состояние для выбора среди вариантов

class InventoryStates(StatesGroup):
    Inventory = State() # Состояние открытого инвентаря
    InventorySearch = State() # Состояние поиска в инвентаре
    InventorySetFilters = State()


def add_if_not(data: dict, userid: int, chatid: int, lang: str):
    """Добавляет минимальные данные для работы"""
    if 'userid' not in data: data['userid'] = userid
    if 'chatid' not in data: data['chatid'] = chatid
    if 'lang' not in data: data['lang'] = lang
    return data


async def ChooseDinoState(function, userid: int, chatid: int, 
        lang: str, add_egg: bool=True, transmitted_data: dict={}):
    """ Устанавливает состояние ожидания динозавра

       В переданную функцию передаёт 
       >>> element: Dino | Egg, transmitted_data: dict
    """
    user = User(userid)
    elements = user.get_dinos
    if add_egg: elements += user.get_eggs
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    ret_data = get_answer_keyboard(elements, lang)

    if ret_data['case'] == 0:
        await bot.send_message(user.userid, 
            t('p_profile.no_dinos_eggs', lang))

    elif ret_data['case'] == 1: #1 динозавр / яйцо, передаём инфу в функцию
        element = ret_data['element']
        await function(element, transmitted_data)

    elif ret_data['case'] == 2:# Несколько динозавров / яиц
        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, GeneralStates.ChooseDino, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['dino_names'] = ret_data['data_names']
            data['transmitted_data'] = transmitted_data

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=ret_data['keyboard'])

async def ChooseIntState(function, userid: int, 
                         chatid: int, lang: str,
                         min_int: int = 1, max_int: int = 10,
                         transmitted_data: dict = {}):
    """ Устанавливает состояние ожидания числа

        В переданную функцию передаёт 
        >>> number: int, transmitted_data: dict
    """
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseInt, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
        data['min_int'] = min_int
        data['max_int'] = max_int

async def ChooseStringState(function, userid: int, 
                         chatid: int, lang: str,
                         min_len: int = 1, max_len: int = 10,
                         transmitted_data: dict = {}):
    """ Устанавливает состояние ожидания сообщения

        В переданную функцию передаёт 
        >>> string: str, transmitted_data: dict
    """
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseString, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
        data['min_len'] = min_len
        data['max_len'] = max_len

async def ChooseConfirmState(function, userid: int, 
                         chatid: int, lang: str,
                         transmitted_data: dict = {}):
    """ Устанавливает состояние ожидания подтверждения действия

        В переданную функцию передаёт 
        >>> answer: bool, transmitted_data: dict
    """
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseConfirm, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data

async def ChooseOptionState(function, userid: int, 
                         chatid: int, lang: str,
                         options: dict = {},
                         transmitted_data: dict = {}):
    """ Устанавливает состояние ожидания выбора опции

        В переданную функцию передаёт 
        >>> answer: ???, transmitted_data: dict
    """
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseOption, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
        data['options'] = options