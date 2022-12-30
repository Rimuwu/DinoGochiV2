import asyncio

import config
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

bot = AsyncTeleBot(config.conf.bot_token, state_storage=StateMemoryStorage())

if __name__ == '__main__':
    print('start')
    asyncio.run(bot.infinity_polling())
