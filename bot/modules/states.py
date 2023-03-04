from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.types import Message

from bot.exec import bot
from bot.modules.localization import t
from bot.modules.markup import get_answer_keyboard
from bot.modules.user import User


class DinoStates(StatesGroup):
    choose_dino = State()

class SettingsStates(StatesGroup):
    settings_choose = State()
    rename_dino_step_name = State()
    rename_dino_step_confirmation = State()


async def dino_answer(function, userid: int, chatid: int, 
        lang: str, add_egg: bool=True, transmitted_data: dict={}):
    """Общая подготовительная функция для выбора динозавра
       В переданную функцию передаёт 
       >>> element: Dino | Egg, data: dict
    """
    user = User(userid)
    elements = user.get_dinos()
    if add_egg: elements += user.get_eggs()

    ret_data = get_answer_keyboard(elements, lang)

    if ret_data['case'] == 0:
        await bot.send_message(user.userid, 
            t('p_profile.no_dinos_eggs', lang))

    elif ret_data['case'] == 1: #1 динозавр / яйцо, передаём инфу в функцию
        element = ret_data['element']
        await function(element, transmitted_data)

    elif ret_data['case'] == 2:# Несколько динозавров / яиц
        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, DinoStates.choose_dino, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['dino_names'] = ret_data['data_names']
            data['data'] = transmitted_data

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=ret_data['keyboard'])