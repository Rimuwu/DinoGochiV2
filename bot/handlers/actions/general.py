from random import randint
from time import time

from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.accessory import check_accessory
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str)
from bot.modules.dinosaur import (Dino, end_collecting, end_game, end_sleep,
                                  start_sleep)
from bot.modules.friends import send_action_invite
from bot.modules.images import dino_collecting, dino_game, dino_journey
from bot.modules.inline import inline_menu
from bot.modules.inventory_tools import start_inv
from bot.modules.item import counts_items
from bot.modules.item import get_data as get_item_data
from bot.modules.item import get_name
from bot.modules.item_tools import use_item
from bot.modules.localization import get_data, t
from bot.modules.markup import count_markup, feed_count_markup
from bot.modules.markup import cancel_markup, markups_menu as m
from bot.modules.mood import add_mood, check_breakdown, check_inspiration
from bot.modules.states_tools import (ChooseIntState, ChooseOptionState,
                                      ChooseDinoState, ChooseStepState)
from bot.modules.user import User, count_inventory_items, premium
from bot.modules.friend_tools import start_friend_menu
from bot.handlers.actions.game import start_game_ent

users = mongo_client.bot.users
items = mongo_client.bot.items
dinosaurs = mongo_client.bot.dinosaurs
sleep_task = mongo_client.tasks.sleep
game_task = mongo_client.tasks.game
collecting_task = mongo_client.tasks.collecting


@bot.message_handler(textstart='commands_name.actions.dino_button')
async def edit_dino_buttom(message: Message):
    """ Изменение последнего динозавра (команда)
    """
    user_id = message.from_user.id
    user = User(user_id)
    dinos = user.get_dinos()
    data_names = {}

    for element in dinos:
        txt = f'🦕 {element.name}'
        data_names[txt] = f'edit_dino {element.alt_id}'
    
    inline = list_to_inline([data_names], 2)
    await bot.send_message(user_id, 
                           t('edit_dino_button.edit', message.from_user.language_code), 
                           reply_markup=inline)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_dino'))
async def answer_edit(callback: CallbackQuery):
    """ Изменение последнего динозавра (кнопка)
    """
    user_id = callback.from_user.id
    lang = callback.from_user.language_code
    user = User(user_id)

    message = callback.message
    data = callback.data.split()[1]

    await bot.delete_message(user_id, message.id)
    dino = dinosaurs.find_one({'alt_id': data}, {'_id': 1, 'name': 1})
    if dino:
        user.update({'$set': {'settings.last_dino': dino['_id']}})
        await bot.send_message(user_id, 
                t('edit_dino_button.susseful', lang, name=dino['name']),
                reply_markup=m(user_id, 'actions_menu', lang, True))

async def invite_adp(friend, transmitted_data: dict):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    action = transmitted_data['action']
    dino_alt = transmitted_data['dino_alt']
    
    await send_action_invite(userid, friend.id, action, dino_alt, lang)
    # Возврат в меню
    await bot.send_message(chatid, t('back_text.actions_menu', lang), reply_markup=m(userid, 'last_menu', lang))

@bot.callback_query_handler(func=
                            lambda call: call.data.startswith('invite_to_action'))
async def invite_to_action(callback: CallbackQuery):
    lang = callback.from_user.language_code
    chatid = callback.message.chat.id
    userid = callback.from_user.id
    data = callback.data.split()
    
    transmitted_data = {
        'action': data[1],
        'dino_alt': data[2]
    }

    dino = dinosaurs.find_one({'alt_id': data[2]})
    if dino:
        res = game_task.find_one({'dino_id': dino['_id']})
        if res: 
            await start_friend_menu(invite_adp, userid, chatid, lang, True, transmitted_data)

            text = t('invite_to_action', lang)
            await bot.send_message(chatid, text, parse_mode='Markdown')

async def join_adp(dino: Dino, transmitted_data):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    
    action = transmitted_data['action']
    friend_dino = transmitted_data['friend_dino']
    friend = transmitted_data['friendid']
    text = ''

    if dino.alt_id == friend_dino:
        text = t('join_to_action.one_dino', lang)
    elif dino.status != 'pass':
        text = t('alredy_busy', lang)

    if text:
        await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=m(userid, 'last_menu', lang))
    
    else:
        if action == 'game':
            await start_game_ent(userid, chatid, lang, 
                                 dino, friend, True, friend_dino)

@bot.callback_query_handler(func=
                            lambda call: call.data.startswith('join_to_action'))
async def join(callback: CallbackQuery):
    lang = callback.from_user.language_code
    chatid = callback.message.chat.id
    userid = callback.from_user.id
    data = callback.data.split()

    action = data[1]
    friend_dino = data[2]
    friendid = data[3]
    
    dino = dinosaurs.find_one({'alt_id': friend_dino})
    if dino:
        res = game_task.find_one({'dino_id': dino['_id']})
        if not res: 
            text = t('entertainments.join_end', lang)
            await bot.send_message(chatid, text)
        else:
            transmitted_data = {
                'action': action,
                'friend_dino': friend_dino,
                'friendid': friendid
            }

            await ChooseDinoState(join_adp, userid, chatid, lang, False, transmitted_data=transmitted_data)