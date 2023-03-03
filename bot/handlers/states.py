
from telebot.types import Message

from bot.exec import bot
from bot.modules.logs import log
from bot.modules.markup import markups_menu as m
from bot.modules.states import DinoStates


@bot.message_handler(text='buttons_name.cancel', state='*')
async def cancel(message: Message):
    """Состояние отмены
    """
    await bot.send_message(message.chat.id, "❌", 
                           reply_markup=m(message.from_user.id, 
                           'last_menu', message.from_user.language_code))
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)

@bot.message_handler(commands=['state'])
async def get_state(message: Message):
    """Состояние
    """
    state = await bot.get_state(message.from_user.id, message.chat.id)
    await bot.send_message(message.chat.id, f'{state}')
    async with bot.retrieve_data(message.from_user.id, 
                                 message.chat.id) as data: 
        log(data)

@bot.message_handler(state=DinoStates.choose_dino, is_authorized=True)
async def answer_dino(message: Message):
    """Общая функция для выбора динозавра
    """
    userid = message.from_user.id

    async with bot.retrieve_data(userid, message.chat.id) as data:
        ret_data = data['dino_names']
        func = data['function']
        data = data['data']

    await bot.delete_state(userid, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)

    if message.text in ret_data.keys():
        await func(ret_data[message.text], data=data)
    else:
        await bot.send_message(message.chat.id, "❌", 
                    reply_markup=m(message.from_user.id, 
                    'last_menu', message.from_user.language_code))