from telebot.asyncio_handler_backends import State, StatesGroup
from bot.exec import bot


@bot.message_handler(text='buttons_name.cancel', state='*')
async def any_state(message):
    """
    Состояние отмены
    """

    await bot.send_message(message.chat.id, "❌")
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)

    #Дописать сюда возвращение к последней клавиатуре

@bot.message_handler(commands=['state'])
async def get_state(message):
    """
    Состояние
    """
    state = await bot.get_state(message.from_user.id, message.chat.id)
    await bot.send_message(message.chat.id, f'{state}')