# Исполнитель бота

import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from bot.modules.logs import log, create_log
from bot.config import conf

bot = AsyncTeleBot(conf.bot_token, state_storage=StateMemoryStorage())

def run():
    create_log()
    log('start')

    # заготовка поддержки асинхронных потоков
    ioloop = asyncio.get_event_loop()

    tasks = [
        ioloop.create_task(bot.infinity_polling())
    ]

    wait_tasks = asyncio.wait(tasks)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()
