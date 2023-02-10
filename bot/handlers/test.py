# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.data_format import near_key_number

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    await bot.send_message(message.from_user.id, near_key_number(n=6, data={'10': 'много', '5': 'средне', '2': 'мало'}))