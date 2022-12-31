from bot import config

from telebot import types
from bot.exec import bot

@bot.message_handler(commands=["test"])
async def start_command(message: types.Message):
    await bot.send_message(message.chat.id, str(config.mongo_client.server_info()))

