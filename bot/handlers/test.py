# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.localization import t, get_all_locales

from bot.modules.user import User


@bot.message_handler(text='buttons_name.back')
async def back_command(message: Message):
    await bot.send_message(message.chat.id, t('language_name', message.from_user.language_code))


@bot.message_handler(content_types=['text'], func=lambda message: message.text == 'local_test')
async def local_test_command(message: Message):
    loc = t('start_game', 'ru')
    print(loc)
    

@bot.message_handler(content_types=['text'], func=lambda message: message.text == 'user_data')
async def user_data_command(message: Message):
    user = User(message.from_user.id)

    dinos = user.get_dinos()
    inv = user.get_inventory()

    for i in dinos:
        print(i.__dict__)
    
    print(inv)


