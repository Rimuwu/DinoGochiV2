from datetime import datetime, timedelta
from time import time

from telebot.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from bot.config import conf, mongo_client
from bot.const import GAME_SETTINGS as GS
from bot.exec import bot
from bot.modules.data_format import list_to_inline, seconds_to_str
from bot.modules.dinosaur import Dino, create_dino_connection
from bot.modules.friend_tools import start_friend_menu
from bot.modules.friends import get_frineds, insert_friend_connect
from bot.modules.item import counts_items
from bot.modules.localization import get_data, t, get_lang
from bot.modules.markup import cancel_markup, confirm_markup, count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.notifications import user_notification
from bot.modules.states_tools import (ChooseConfirmState, ChooseCustomState,
                                      ChooseDinoState, ChooseIntState,
                                      ChoosePagesState, ChooseStepState)
from bot.modules.user import (AddItemToUser, check_name, daily_award_con,
                              take_coins, user_in_chat, user_name)

events = mongo_client.tasks.events

@bot.message_handler(text='commands_name.dino_tavern.events', is_authorized=True)
async def events_c(message: Message):
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id

    text = t('events.info', lang)

    res = list(events.find({}))
    a = 0
    for event in res:
        a += 1

        if event['type'] == 'time_year':
            season = event['data']['season']
            event_text = t(f"events.time_year.{season}", lang)
        else: event_text = t(f"events.{event['type']}", lang)
        text += f'{a}. {event_text}\n\n'

    await bot.send_message(chatid, text)

async def bonus_message(user, message, lang):
    userid = message.from_user.id

    add_text = ''
    award_data = GS['daily_award']
    markup_inline = InlineKeyboardMarkup()

    lvl1 = counts_items(award_data['lvl1']['items'], lang) \
        + f', ' + str(award_data['lvl1']['coins'])

    lvl2 = counts_items(award_data['lvl2']['items'], lang) \
        + f', ' + str(award_data['lvl2']['coins'])

    res = await user_in_chat(userid, -1001673242031)
    res2 = check_name(message.from_user)

    if res: add_text += t('daily_award.2', lang)
    else: add_text += t('daily_award.1', lang)
    if res2: add_text += t('daily_award.bonus', lang)

    text = t('daily_award.info', lang, lvl_1=lvl1, lvl_2=lvl2)
    if not res2:
        name_dino = f'{user.full_name} loves *DinoGochi* / {user.first_name} 🦕 *DinoGochi*'
        bonus = counts_items(award_data['bonus']['items'], lang) \
        + f', ' + str(award_data['bonus']['coins'])

        text += t('daily_award.bonus_text', lang, name_dino=name_dino, bonus=bonus)

    text += t('daily_award.lvl_now', lang) + add_text
    award = t('daily_award.buttons.activate', lang)

    if not res:
        url_b = t('daily_award.buttons.channel_url', lang)
        markup_inline.add(InlineKeyboardButton(text=url_b, 
                            url='https://t.me/DinoGochi'))
    if not res2:
        rename = t('daily_award.buttons.rename', lang)
        markup_inline.add(InlineKeyboardButton(text=rename, 
                            url='tg://settings/edit_profile'))

    markup_inline.add(InlineKeyboardButton(text=award, 
                            callback_data='daily_award'))

    photo = open('images/remain/taverna/dino_reward.png', 'rb')
    await bot.send_photo(message.chat.id, photo, 
            text, parse_mode='Markdown', reply_markup=markup_inline)

@bot.message_handler(text='commands_name.dino_tavern.daily_award', is_authorized=True)
async def bonus(message: Message):
    lang = get_lang(message.from_user.id)
    user = message.from_user
    await bonus_message(user, message, lang)

@bot.callback_query_handler(func=lambda call: 
    call.data == 'daily_message', is_authorized=True)
async def daily_message(callback: CallbackQuery):
    user = callback.from_user
    lang = get_lang(callback.from_user.id)
    message = callback.message
    await bonus_message(user, message, lang)

@bot.callback_query_handler(func=lambda call: call.data == 'daily_award', is_authorized=True)
async def daily_award(callback: CallbackQuery):
    chatid = callback.message.chat.id
    userid = callback.from_user.id
    lang = get_lang(callback.from_user.id)

    if sec := daily_award_con(userid):
        award_data = GS['daily_award']
        res = await user_in_chat(userid, -1001673242031)

        key, add_bonus = 'lvl1', check_name(callback.from_user)
        if res: key = 'lvl2'

        items = []
        items = award_data[key]['items']
        coins = award_data[key]['coins']
        if add_bonus:
            items += award_data['bonus']['items']
            coins += award_data['bonus']['coins']

        str_items = counts_items(items, lang)
        strtime = seconds_to_str(sec - int(time()), lang)

        text = t('daily_award.use', lang, time=strtime, 
                 items=str_items, coins=coins)
        await bot.send_message(chatid, text, parse_mode='Markdown')

        for i in items: AddItemToUser(userid, i)
        take_coins(userid, coins, True)
    else:
        text = t('daily_award.in_base', lang)
        await bot.send_message(chatid, text, parse_mode='Markdown')
