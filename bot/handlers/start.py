import time
from random import choice

from telebot import types

from bot.exec import bot
from bot.modules.data_format import list_to_keyboard, user_name
from bot.modules.dinosaur import insert_dino
from bot.modules.images import create_eggs_image
from bot.modules.localization import t
from bot.modules.markup import markups_menu as m
from bot.modules.user import insert_user

stickers = bot.get_sticker_set('Stickers_by_DinoGochi_bot')


@bot.message_handler(commands=['start'], is_authorized=True)
async def start_command_auth(message: types.Message):
    stickers = await bot.get_sticker_set('Stickers_by_DinoGochi_bot')
    sticker = choice(list(stickers.stickers)).file_id
    await bot.send_sticker(message.chat.id, sticker)

@bot.message_handler(commands=['start'], is_authorized=False)
async def start_game_message(message: types.Message):
    langue_code = message.from_user.language_code
    username = user_name(message.from_user)

    text = t('start_command.first_message', langue_code, username=username)
    buttons_list = [t('commands_name.start_game', locale=langue_code)]
    markup = list_to_keyboard(buttons_list)
    
    await bot.send_message(message.from_user.id, text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(text='commands_name.start_game', is_authorized=False)
async def start_game(message: types.Message):

    #Сообщение-реклама
    text = t('start_command.request_subscribe.text', message.from_user.language_code)
    b1, b2 = t('start_command.request_subscribe.buttons', message.from_user.language_code)

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(types.InlineKeyboardButton(text=b1, url='https://t.me/DinoGochi'))
    markup_inline.add(types.InlineKeyboardButton(text=b2, url='https://t.me/+pq9_21HXXYY4ZGQy'))

    await bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup_inline)

    #Создание изображения
    photo, id_l = create_eggs_image()

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(*[types.InlineKeyboardButton(
            text=f'🥚 {id_l.index(i) + 1}', 
            callback_data=f'egg_answer {i}') for i in id_l]
    )

    start_game = str(t('start_command.start_game', message.from_user.language_code))
    await bot.send_photo(message.chat.id, photo, start_game, reply_markup=markup_inline)


@bot.callback_query_handler(func=None, startwith='egg_answer', is_authorized=False)
async def egg_answer_callback(callback: types.CallbackQuery):
    egg_id = int(callback.data.split()[1])

    #Создание юзера
    insert_user(callback.from_user.id, callback.from_user.language_code)
    insert_dino(egg_id, callback.from_user.id)

    edited_text = t('start_command.end_answer.edited_text', callback.from_user.language_code, egg_id=egg_id)
    send_text = t('start_command.end_answer.send_text', callback.from_user.language_code)

    await bot.edit_message_caption(edited_text, callback.message.chat.id, callback.message.message_id)

    await bot.send_message(callback.message.chat.id, send_text, parse_mode='Markdown', reply_markup=m())