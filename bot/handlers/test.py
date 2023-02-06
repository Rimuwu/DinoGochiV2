# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.data_format import seconds_to_str

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    import random
    await bot.send_message(message.from_user.id, seconds_to_str(random.randint(1, 100000), 'ru', True))