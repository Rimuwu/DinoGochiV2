# Исполнитель бота

import traceback

from telebot.async_telebot import AsyncTeleBot, ExceptionHandler
from telebot.asyncio_storage import StateMemoryStorage

from bot.config import conf
from bot.modules.logs import log
from bot.taskmanager import add_task, run as run_taskmanager

class TracebackHandler(ExceptionHandler):
    def handle(self, exception):
        log(traceback.format_exc(), 3)

bot = AsyncTeleBot(conf.bot_token, state_storage=StateMemoryStorage(), exception_handler=TracebackHandler(), colorful_logs=True)

def run():
    log('Привет! Я вижу ты так и не починил тот самый баг на 46-ой строчке...')
    log('Это не баг, а фича!')
    log('Ваша фича наминирована на оскар!')
    log('Спасибо, но я все равно перепишу все с нуля...')

    add_task(bot.infinity_polling)
    log('Все готово! Взлетаем!', prefix='🟢 ')
    run_taskmanager()
