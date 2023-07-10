from random import choice

from telebot import types

from bot.config import mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.handlers.states import cancel
from bot.modules.data_format import list_to_keyboard, seconds_to_str, user_name
from bot.modules.dinosaur import incubation_egg
from bot.modules.images import create_eggs_image
from bot.modules.localization import get_data, t, get_lang
from bot.modules.markup import markups_menu as m
from bot.modules.user import insert_user
from bot.modules.referals import connect_referal
from bot.handlers.referal_menu import check_code

stickers = bot.get_sticker_set('Stickers_by_DinoGochi_bot')
referals = mongo_client.connections.referals

@bot.message_handler(commands=['start'], is_authorized=True)
async def start_command_auth(message: types.Message):
    stickers = await bot.get_sticker_set('Stickers_by_DinoGochi_bot')
    sticker = choice(list(stickers.stickers)).file_id

    lang = get_lang(message.from_user.id)
    await bot.send_sticker(message.chat.id, sticker, 
                           reply_markup=m(message.from_user.id, language_code=lang))

    await cancel(message, '')

    content = str(message.text).split()
    if len(content) > 1: 
        referal = str(content[1])
        await check_code(referal, 
                         {'userid': message.from_user.id,
                          'chatid': message.chat.id,
                          'lang': get_lang(message.from_user.id)})

@bot.message_handler(text='commands_name.start_game', is_authorized=False)
async def start_game(message: types.Message, referal: str = ''):

    #Сообщение-реклама
    text = t('start_command.request_subscribe.text', message.from_user.language_code)
    b1, b2 = get_data('start_command.request_subscribe.buttons', message.from_user.language_code)

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(types.InlineKeyboardButton(text=b1, url='https://t.me/DinoGochi'))
    markup_inline.add(types.InlineKeyboardButton(text=b2, url='https://t.me/+pq9_21HXXYY4ZGQy'))

    await bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup_inline)

    #Создание изображения
    img, id_l = create_eggs_image()

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(*[types.InlineKeyboardButton(
            text=f'🥚 {id_l.index(i) + 1}', 
            callback_data=f'start_egg {i} {referal}') for i in id_l]
    )

    start_game = t('start_command.start_game', message.from_user.language_code)
    await bot.send_photo(message.chat.id, img, start_game, reply_markup=markup_inline)

@bot.message_handler(commands=['start'], is_authorized=False)
async def start_game_message(message: types.Message):
    langue_code = message.from_user.language_code
    username = user_name(message.from_user)
    
    content = str(message.text).split()
    add_referal = False
    markup = None
    
    if len(content) > 1: 
        referal = str(content[1])
        if referals.find_one({'code': referal}): add_referal = True

    if not add_referal:
        buttons_list = [get_data('commands_name.start_game', locale=langue_code)]
        markup = list_to_keyboard(buttons_list)

    image = open('images/remain/start/placeholder.png', 'rb')
    text = t('start_command.first_message', langue_code, username=username)
    
    await bot.send_photo(message.chat.id, image, text, reply_markup=markup, parse_mode='HTML')
    
    if add_referal:
        text = t('start_command.referal', langue_code, username=username)
        await bot.send_message(message.chat.id, text)

        await start_game(message, referal=referal) # type: ignore


@bot.callback_query_handler(is_authorized=False, 
                            func=lambda call: call.data.startswith('start_egg'))
async def egg_answer_callback(callback: types.CallbackQuery):
    egg_id = int(callback.data.split()[1])
    lang = callback.from_user.language_code

    # Сообщение
    edited_text = t('start_command.end_answer.edited_text', lang)
    send_text = t('start_command.end_answer.send_text', lang, inc_time=
                  seconds_to_str(GAME_SETTINGS['first_dino_time_incub'], lang))

    await bot.edit_message_caption(edited_text, callback.message.chat.id, callback.message.message_id)
    await bot.send_message(callback.message.chat.id, send_text, parse_mode='Markdown', 
                           reply_markup=m(callback.from_user.id, language_code=lang))

    # Создание юзера и добавляем динозавра в инкубацию
    insert_user(callback.from_user.id, lang)
    incubation_egg(egg_id, callback.from_user.id, quality=GAME_SETTINGS['first_egg_rarity'])

    if len(callback.data.split()) > 2:
        referal = callback.data.split()[2]
        connect_referal(referal, callback.from_user.id)