# Исполнитель бота

import asyncio
from bot import config

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from bot.modules.logs import LogFuncs

bot = AsyncTeleBot(config.conf.bot_token, state_storage=StateMemoryStorage())
log = LogFuncs()

def run():
    log.create_log()
    log.console_message('start')
    asyncio.run(bot.infinity_polling())
