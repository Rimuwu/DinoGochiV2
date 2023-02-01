from telebot import types

from bot.exec import bot
from bot.modules.user import User


@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def start_game(message: types.Message):
    user = User(message.from_user.id)
    print(user.get_dinos())