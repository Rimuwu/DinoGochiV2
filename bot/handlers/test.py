# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.notifications import user_notification

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    await user_notification(message.from_user.id, 'test')

