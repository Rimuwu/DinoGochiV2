# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from ..modules.data_format import random_quality

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    d = 0
    for i in range(100):
        if random_quality() == 'com': d+=1
    await bot.send_message(message.chat.id, str(d))

