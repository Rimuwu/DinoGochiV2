from telebot import types

from bot.exec import bot
from bot.modules.user import User
from bot.modules.localization import t


@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def dino_profile(message: types.Message):
    user = User(message.from_user.id)
    elements = user.get_dinos() + user.get_eggs()

    if len(elements) == 0:
        await bot.send_message(user.userid, t('p_profile.no_dinos_eggs'), message)
    elif len(elements) == 1:
        ...
    else:
        ...