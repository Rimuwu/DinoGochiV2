from random import choice
from telebot import types

from bot.exec import bot
from bot.modules.user import User, insert_user
from bot.modules.localization import t
from bot.modules.images import create_eggs_image


@bot.message_handler(commands=['start'], is_authorized=True)
async def start_command_auth(message: types.Message):
    stickers = await bot.get_sticker_set('Stickers_by_DinoGochi_bot')
    sticker = choice(list(stickers.stickers)).file_id
    await bot.send_sticker(message.chat.id, sticker)


@bot.message_handler(commands=['start'], is_authorized=False)
async def start_game(message: types.Message):
    user = User(message.from_user.id)

    text = t('request_subscribe.text', message.from_user.language_code)
    b1, b2 = t('request_subscribe.button', message.from_user.language_code)
    start_game = t('start_game', message.from_user.language_code)

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(types.InlineKeyboardButton(text=b1, url='https://t.me/DinoGochi'))
    markup_inline.add(types.InlineKeyboardButton(text=b2, url='https://t.me/+pq9_21HXXYY4ZGQy'))

    await bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup_inline)

    photo, id_l = create_eggs_image()

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(*[types.InlineKeyboardButton(
            text=f'🥚 {id_l.index(i) + 1}', 
            callback_data=f'egg_answer {i}') for i in id_l]
    )

    await bot.send_photo(message.chat.id, photo, start_game, reply_markup=markup_inline)
    insert_user(user.id, message.from_user.language_code)


@bot.callback_query_handler(func=None, startwith='egg_answer')
async def egg_answer_callback(callback: types.CallbackQuery):
    id = callback.data.split(' ')[1]

    await bot.send_message(callback.from_user.id, id)