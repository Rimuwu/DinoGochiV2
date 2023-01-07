# Тестовые команды

from telebot import types
from bot.exec import bot
from bot.modules.localization import t, get_all_locales

from bot.modules.user import User


@bot.message_handler(text="buttons_name.back")
async def back_command(message: types.Message):
    await bot.send_message(message.chat.id, t("language_name", message.from_user.language_code))


@bot.message_handler(content_types=['text'], func=lambda message: message.text == 'local_test')
async def on_message(message):
    loc = t('start_game', 'ru')
    print(loc)
    

@bot.message_handler(content_types=['text'], func=lambda message: message.text == 'user_data')
async def on_message(message):
    user = message.from_user

    dinos = User(user.id).get_dinos()
    inv = User(user.id).get_inventory()

    for i in dinos:
        print(i.__dict__)
    
    print(inv)


