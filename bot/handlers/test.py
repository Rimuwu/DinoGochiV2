from bot import config

from telebot import types
from bot.exec import bot
from bot.modules.localization import t


@bot.message_handler(text="buttons_name.back")
async def back_command(message: types.Message):
    await bot.send_message(message.chat.id, t("language_name", message.from_user.language_code))

