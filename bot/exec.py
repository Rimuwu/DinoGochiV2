# Исполнитель бота

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from bot.config import conf
from bot.modules.logs import create_log, log
from bot.tasks.taskmanager import add_task, run as run_taskmanager

bot = AsyncTeleBot(conf.bot_token, state_storage=StateMemoryStorage())

def run():
    create_log()
    log('Привет! Я вижу ты так и не починил тот самый баг на 46-ой строчке...')
    log('Это не баг, а фича!')
    log('Ваша фича наминирована на оскар!')

    add_task(bot.infinity_polling)
    run_taskmanager()
