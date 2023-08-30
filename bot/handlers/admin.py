from telebot.types import CallbackQuery, Message

from bot.config import mongo_client, conf
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.states_tools import start_friend_menu
from bot.modules.friends import get_frineds, insert_friend_connect
from bot.modules.localization import get_data, t, get_lang
from bot.modules.markup import cancel_markup, confirm_markup, count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.notifications import user_notification
from bot.modules.states_tools import (ChooseConfirmState, ChooseCustomState,
                                      ChoosePagesState, ChooseDinoState, ChooseStepState, ChooseStringState)
from bot.modules.user import user_name, take_coins
from bot.modules.dinosaur import Dino, create_dino_connection
from bot.modules.states_tools import (ChooseOptionState, ChoosePagesState,
                                      ChooseStepState, prepare_steps, ChooseStringState)
from bot.modules.tracking import creat_track, get_track_pages, track_info
from bot.modules.promo import create_promo_start, get_promo_pages, promo_ui, use_promo
from time import time

management = mongo_client.other.management
promo = mongo_client.other.promo

users = mongo_client.user.users
friends = mongo_client.user.friends
dinosaurs = mongo_client.dinosaur.dinosaurs
dino_owners = mongo_client.dinosaur.dino_owners

@bot.message_handler(commands=['send_message'], is_admin=True)
async def send_message(message: Message):
    chatid = message.chat.id
    lang = get_lang(message.from_user.id)
    
    # Рассылка

@bot.message_handler(commands=['create_tracking'], is_admin=True)
async def create_tracking(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)

    await ChooseStringState(create_track, userid, chatid, lang, 1, 0)
    await bot.send_message(chatid, t("create_tracking.name", lang), parse_mode='Markdown')

async def create_track(name, transmitted_data: dict):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']

    res, text = creat_track(name.lower()), '-'
    if res == 1:
        iambot = await bot.get_me()
        bot_name = iambot.username

        url = f'https://t.me/{bot_name}/?promo={name}'
        text = t("create_tracking.ok", lang, url=url)
    elif res == 0: text = 'error no document'
    elif res == -1: text = 'error name no find'
    elif res == -2: text = t("create_tracking.already", lang)

    await bot.send_message(chatid, text, parse_mode='Markdown')

@bot.message_handler(commands=['tracking'], is_admin=True)
async def tracking(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)

    options = get_track_pages()
    res = await ChoosePagesState(track_info_adp, userid, chatid, lang, options, one_element=False, autoanswer=False)
    await bot.send_message(chatid, t("track_open", lang), parse_mode='Markdown')

async def track_info_adp(data, transmitted_data: dict):
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']

    text, markup = await track_info(data, lang)
    await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('track'), private=True)
async def track(call: CallbackQuery):
    split_d = call.data.split()
    action = split_d[1]
    code = split_d[2]

    chatid = call.message.chat.id
    lang = get_lang(call.from_user.id)

    res = management.find_one({'_id': 'tracking_links'})
    if res:
        text = '-'
        if action == 'delete':
            text = t("track_delete", lang)
            management.update_one({'_id': 'tracking_links'}, 
                                {'$unset': {f'links.{code}': 0}})

        elif action == 'clear':
            text = t("track_clear", lang)
            management.update_one({'_id': 'tracking_links'}, 
                                {'$set': {f'links.{code}.col': 0}})

        await bot.send_message(chatid, text)

@bot.message_handler(commands=['create_promo'], is_admin=True)
async def create_promo(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)

    await create_promo_start(userid, chatid, lang)

@bot.message_handler(commands=['promos'], is_admin=True)
async def promos(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)

    options = get_promo_pages()
    res = await ChoosePagesState(promo_info_adp, userid, chatid, lang, options, one_element=False, autoanswer=False)
    await bot.send_message(chatid, t("promo_commands.promo_open", lang), parse_mode='Markdown')

async def promo_info_adp(code, transmitted_data: dict):
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']

    text, markup = promo_ui(code, lang)
    await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('promo'))
async def promo_call(call: CallbackQuery):
    split_d = call.data.split()
    action = split_d[2]
    code = split_d[1]

    userid = call.from_user.id
    chatid = call.message.chat.id
    lang = get_lang(call.from_user.id)

    res = promo.find_one({"code": code})
    if res:
        if action in ['activ', 'delete'] and userid in conf.bot_devs:
            
            if action == 'activ':
                if not res['active']:
                    res['active'] = True

                    if res['time'] != 'inf':
                        res['time_end'] = int(time()) + res['time']

                else:
                    res['active'] = False
                    if res['time'] != 'inf':
                        res['time'] = res['time_end'] - int(time())
                        res['time_end'] = 0

                management.update_one({"code": code}, {"$set": res})

                text, markup = promo_ui(code, lang)
                await bot.edit_message_text(text, chatid, call.message.message_id, reply_markup=markup, parse_mode='markdown')

        elif action == 'use':
            status, text = use_promo(code, userid, lang)
            await bot.send_message(chatid, text, parse_mode='Markdown')