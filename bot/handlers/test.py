# Тестовые команды

from bot import config

from telebot import types
from bot.exec import bot
from bot.modules.localization import t, get_all_locales


@bot.message_handler(text="buttons_name.back")
async def back_command(message: types.Message):
    await bot.send_message(message.chat.id, t("language_name", message.from_user.language_code))


@bot.message_handler(content_types=['text'], func=lambda message: message.text == '+')
async def on_message(message):
    user = message.from_user
    locales = get_all_locales('language_name')

    for key in locales:
        await bot.send_message(message.chat.id, t("language_name", key))

