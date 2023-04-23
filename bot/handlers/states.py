
from telebot.types import Message

from bot.exec import bot
from bot.modules.logs import log
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import GeneralStates
from bot.modules.localization import t, get_data

async def cancel(message, text:str = "❌"):
    if text:
        await bot.send_message(message.chat.id, text, 
            reply_markup=m(message.from_user.id, 'last_menu', message.from_user.language_code))
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)

@bot.message_handler(text='buttons_name.cancel', state='*')
async def cancel_m(message: Message):
    """Состояние отмены
    """
    await cancel(message)

@bot.message_handler(commands=['cancel'], state='*')
async def cancel_c(message: Message):
    """Команда отмены
    """
    await cancel(message)


@bot.message_handler(commands=['state'])
async def get_state(message: Message):
    """Состояние
    """
    state = await bot.get_state(message.from_user.id, message.chat.id)
    await bot.send_message(message.chat.id, f'{state}')
    try:
        async with bot.retrieve_data(message.from_user.id, 
                                 message.chat.id) as data: log(data)
    except: pass

@bot.message_handler(state=GeneralStates.ChooseDino, is_authorized=True)
async def ChooseDino(message: Message):
    """Общая функция для выбора динозавра
    """
    userid = message.from_user.id
    lang = message.from_user.language_code

    async with bot.retrieve_data(userid, message.chat.id) as data:
        ret_data = data['dino_names']
        func = data['function']
        transmitted_data = data['transmitted_data']

    if message.text in ret_data.keys():
        await bot.delete_state(userid, message.chat.id)
        await bot.reset_data(message.from_user.id,  message.chat.id)
        await func(ret_data[message.text], transmitted_data=transmitted_data)
    else:
        await bot.send_message(message.chat.id, 
                t('states.ChooseDino.error_not_dino', lang))

@bot.message_handler(state=GeneralStates.ChooseInt, is_authorized=True)
async def ChooseInt(message: Message):
    """Общая функция для ввода числа
    """
    userid = message.from_user.id
    lang = message.from_user.language_code
    number = 0

    async with bot.retrieve_data(userid, message.chat.id) as data:
        min_int: int = data['min_int']
        max_int: int = data['max_int']
        func = data['function']
        transmitted_data = data['transmitted_data']

    if str(message.text).isdigit():
        number = int(message.text) #type: ignore

    elif str(message.text).startswith('x') and \
        str(message.text)[1:].isdigit():
        number = int(message.text[1:]) #type: ignore
    
    else:
        await bot.send_message(message.chat.id, 
                t('states.ChooseInt.error_not_int', lang))
        return
    
    if number > max_int:
        await bot.send_message(message.chat.id, 
                t('states.ChooseInt.error_max_int', lang,
                number = number, max = max_int))
        return

    if number < min_int:
        await bot.send_message(message.chat.id, 
                t('states.ChooseInt.error_min_int', lang,
                number = number, min = min_int))
        return
    
    await bot.delete_state(userid, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)
    await func(number, transmitted_data=transmitted_data)

@bot.message_handler(state=GeneralStates.ChooseString, is_authorized=True)
async def ChooseString(message: Message):
    """Общая функция для ввода сообщения
    """
    userid = message.from_user.id
    lang = message.from_user.language_code

    async with bot.retrieve_data(userid, message.chat.id) as data:
        max_len: int = data['max_len']
        min_len: int = data['min_len']
        func = data['function']
        transmitted_data = data['transmitted_data']

    content = str(message.text)
    content_len = len(content)

    if content_len > max_len:
        await bot.send_message(message.chat.id, 
                t('states.ChooseString.error_max_len', lang,
                number = content_len, max = max_len))
        return

    if content_len < min_len:
        await bot.send_message(message.chat.id, 
                t('states.ChooseString.error_min_len', lang,
                number = content_len, min = min_len))
        return

    await bot.delete_state(userid, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)
    await func(content, transmitted_data=transmitted_data)

@bot.message_handler(state=GeneralStates.ChooseConfirm, is_authorized=True)
async def ChooseConfirm(message: Message):
    """Общая функция для подтверждения
    """
    userid = message.from_user.id
    lang = message.from_user.language_code
    content = str(message.text)

    async with bot.retrieve_data(userid, message.chat.id) as data:
        func = data['function']
        transmitted_data = data['transmitted_data']
        cancel_status = transmitted_data['cancel']

    buttons = get_data('buttons_name', lang)
    buttons_data = {
        buttons['enable']: True,
        buttons['confirm']: True,
        buttons['disable']: False
    }
    
    if content in buttons_data:
        
        if not(buttons_data[content]) and cancel_status:
            await cancel(message)
        else:
            await bot.delete_state(userid, message.chat.id)
            await bot.reset_data(message.from_user.id,  message.chat.id)
            await func(buttons_data[content], transmitted_data=transmitted_data)

    else:
        await bot.send_message(message.chat.id, 
                t('states.ChooseConfirm.error_not_confirm', lang))

@bot.message_handler(state=GeneralStates.ChooseOption, is_authorized=True)
async def ChooseOption(message: Message):
    """Общая функция для выбора из предложенных вариантов
    """
    userid = message.from_user.id
    lang = message.from_user.language_code

    async with bot.retrieve_data(userid, message.chat.id) as data:
        options: dict = data['options']
        func = data['function']
        transmitted_data = data['transmitted_data']

    if message.text in options.keys():
        await bot.delete_state(userid, message.chat.id)
        await bot.reset_data(message.from_user.id,  message.chat.id)
        await func(options[message.text], transmitted_data=transmitted_data)
    else:
        await bot.send_message(message.chat.id, 
                t('states.ChooseOption.error_not_option', lang))