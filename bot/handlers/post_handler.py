"""Файл должен загружаться последним, чтобы сюда попадали только необработанные хендлеры
"""
from telebot import types
from bot.exec import bot
from bot.modules.logs import log
from bot.modules.localization import t


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_message'))
async def delete_message(call: types.CallbackQuery):
    chatid = call.message.chat.id
    await bot.delete_message(chatid, call.message.id)
    await bot.answer_callback_query(call.id, "🗑")

@bot.callback_query_handler(func=lambda call: call.data.startswith(' '))
async def pass_h(call: types.CallbackQuery): pass

@bot.callback_query_handler(func=lambda call: True)
async def not_found(call: types.CallbackQuery):
    userid = call.from_user.id
    log(f'Ключ {call.data} не был обработан! Пользователь: {userid}', 2, "CallbackQuery")

@bot.message_handler(is_authorized=False)
async def not_authorized(message: types.Message):
    lang = message.from_user.language_code
    chatid = message.chat.id

    text = t('not_authorized', lang)
    await bot.send_message(chatid, text)

@bot.message_handler()
async def not_found_text(message: types.Message):
    lang = message.from_user.language_code
    chatid = message.chat.id

    text = t('not_found_key', lang)
    await bot.send_message(chatid, text)