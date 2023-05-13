"""Файл должен загружаться последним, чтобы сюда попадали только необработанные хендлеры
"""
from telebot import types
from bot.exec import bot
from bot.modules.logs import log

@bot.callback_query_handler(func=lambda call: True)
async def not_found(call: types.CallbackQuery):
    userid = call.from_user.id
    log(f'Ключ {call.data} не был обработан! Пользователь: {userid}', 2, "CallbackQuery")