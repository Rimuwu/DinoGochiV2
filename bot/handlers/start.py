from random import choice
from telebot import types

from bot.exec import bot
from bot.modules.user import User, insert_user
from bot.modules.localization import t


@bot.message_handler(commands=['start'], is_authorized=True)
async def start_command_auth(message: types.Message):
    stickers = await bot.get_sticker_set('Stickers_by_DinoGochi_bot')
    sticker = choice(list(stickers.stickers)).file_id
    await bot.send_sticker(message.chat.id, sticker)

@bot.message_handler(commands=['start'], is_authorized=False)
async def start_game(message: types.Message):
    user = User(message.from_user.id)

    if user.data == None:
        text = t('request_subscribe.text', message.from_user.language_code)
        b1, b2 = t('request_subscribe.button', message.from_user.language_code)

        print(text)
        print(b1, b2)

        # markup_inline = types.InlineKeyboardMarkup()

        # markup_inline.add(types.InlineKeyboardButton(text=b1, url='https://t.me/DinoGochi'))
        # markup_inline.add(types.InlineKeyboardButton(text=b2, url='https://t.me/+pq9_21HXXYY4ZGQy'))

        # bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup_inline)

        # text = t('request_subscribe.start_game', message.from_user.language_code)

        # photo, markup_inline, id_l = Functions.create_egg_image()
        # bot.send_photo(message.chat.id, photo, text, reply_markup=markup_inline)

        # insert_user(user.id, message.from_user.language_code)

        # users.update_one({'userid': user.id}, {'$set': {'eggs': id_l}})