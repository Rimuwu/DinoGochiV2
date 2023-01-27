# Исполнитель бота

import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from bot.config import conf
from bot.modules.logs import create_log, log
from bot.tasks.taskmanager import task_dict, task_executor

bot = AsyncTeleBot(conf.bot_token, state_storage=StateMemoryStorage())

def run():
    create_log()
    log('Привет! Я вижу ты так и не починил тот самый баг на 46-ой строчке...')

    # заготовка поддержки асинхронных потоков
    ioloop = asyncio.get_event_loop()

    tasks = [
        ioloop.create_task(bot.infinity_polling())
    ]

    for func, data in task_dict.items():
        tasks.append(
            ioloop.create_task(
                task_executor(function=func, seconds=data[0], wait=data[1])
            )
        )

    wait_tasks = asyncio.wait(tasks)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()
