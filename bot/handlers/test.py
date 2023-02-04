# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.handlers.start import start_game

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    await start_game(message)