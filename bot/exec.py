# Исполнитель бота

import asyncio
from bot import config

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from bot.modules.logs import console_message, create_log

bot = AsyncTeleBot(config.conf.bot_token, state_storage=StateMemoryStorage())

def run():
    create_log()
    console_message('start')
    asyncio.run(bot.infinity_polling())
