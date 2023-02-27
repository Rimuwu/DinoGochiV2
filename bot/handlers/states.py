from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.types import Message

from bot.exec import bot
from bot.modules.markup import markups_menu as m


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
