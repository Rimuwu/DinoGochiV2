# Исполнитель бота

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from bot.config import conf
from bot.modules.logs import create_log, log
from bot.taskmanager import add_task, run as run_taskmanager

bot = AsyncTeleBot(conf.bot_token, state_storage=StateMemoryStorage())

def run():
    create_log()
    log('Привет! Я вижу ты так и не починил тот самый баг на 46-ой строчке...')
    log('Это не баг, а фича!')
    log('Ваша фича наминирована на оскар!')
    log('Спасибо, но я все равно перепишу все с нуля...')

    add_task(bot.infinity_polling)
    log('Все готово! Взлетаем!')
    run_taskmanager()
