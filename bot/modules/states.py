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


async def dino_answer(function, message: Message, add_egg: bool=True):
    """Общая подготовительная функция для выбора динозавра
    """
    user = User(message.from_user.id)
    lang = message.from_user.language_code
    elements = user.get_dinos()
    if add_egg: elements += user.get_eggs()

    ret_data = get_answer_keyboard(elements, lang) #type: ignore

    if ret_data['case'] == 0:
        await bot.send_message(user.userid, 
            t('p_profile.no_dinos_eggs', lang))

    elif ret_data['case'] == 1: #1 динозавр / яйцо, передаём инфу в функцию
        element = ret_data['element']
        await function(message, element)

    elif ret_data['case'] == 2:# Несколько динозавров / яиц
        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, DinoStates.choose_dino, message.chat.id)
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['function'] = function
            data['data'] = ret_data['data_names']

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=ret_data['keyboard'])