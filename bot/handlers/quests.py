from asyncio import sleep
from time import time

from telebot.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, InputMedia, Message)

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline, seconds_to_str
from bot.modules.item import AddItemToUser
from bot.modules.localization import get_data, t
from bot.modules.quests import quest_resampling, quest_ui, check_quest
from bot.modules.user import take_coins

quests_data = mongo_client.bot.quests
users = mongo_client.bot.users

@bot.message_handler(text='commands_name.dino_tavern.quests', is_authorized=True)
async def check_quests(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    
    user = users.find_one({'userid': userid})
    quests = list(quests_data.find({'owner_id': userid}))

    text = t('quest.quest_menu', lang, 
             end=user['dungeon']['quest_ended'], act=len(quests))
    await bot.send_message(chatid, text)

    for quest in quests:
        text, mark = quest_ui(quest, lang, quest['alt_id'])
        await bot.send_message(
                        chatid, text, reply_markup=mark, parse_mode='Markdown')
        await sleep(0.3)

@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('quest'))
async def quest(call: CallbackQuery):
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = call.from_user.language_code
    message = call.message

    data = call.data.split()
    alt_id = data[2]

    quest = quests_data.find_one({'alt_id': alt_id, 'owner_id': userid})
    if quest:
        if int(time()) > quest['time_end']:
            quest_resampling(quest['_id'])

            text = t('quest.time_end_h', lang)
            await bot.send_message(chatid, text)
            await bot.edit_message_reply_markup(chatid, message.id, 
                                   reply_markup=InlineKeyboardMarkup())
        else:
            if data[1] == 'delete':
                quest_resampling(quest['_id'])

                text = t('quest.delete_button', lang)
                mark = list_to_inline([{text: ' '}])
                await bot.edit_message_reply_markup(chatid, message.id, 
                                    reply_markup=mark)
            elif data[1] == 'end':
                result = check_quest(quest)

                if result:
                    text = t('quest.end_quest', lang, author_name=quest['author'], name=quest['name'])

                    b_name = t('quest.end_quest_button', lang)
                    mark = list_to_inline([{b_name: ' '}])

                    await bot.edit_message_reply_markup(chatid, message.id, reply_markup=mark)

                    take_coins(userid, quest['reward']['coins'], True)
                    for i in quest['reward']['items']: 
                        AddItemToUser(userid, i)

                    quests_data.delete_one({'_id': quest['_id']})
                    users.update_one({'userid': userid}, {'$inc': {'dungeon.quest_ended': 1}})

                else: text = t('quest.conditions', lang)

                await bot.send_message(chatid, text, parse_mode='Markdown')
    else:
        text = t('quest.not_found', lang)
        await bot.send_message(chatid, text)
        await bot.edit_message_reply_markup(chatid, message.id, 
                                   reply_markup=InlineKeyboardMarkup())