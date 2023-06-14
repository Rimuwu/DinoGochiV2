from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.friend_tools import start_friend_menu
from bot.modules.friends import get_frineds, insert_friend_connect
from bot.modules.localization import get_data, t
from bot.modules.markup import cancel_markup, confirm_markup, count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.notifications import user_notification
from bot.modules.states_tools import (ChooseConfirmState, ChooseCustomState,
                                      ChoosePagesState, ChooseDinoState, ChooseStepState, ChooseIntState)
from bot.modules.user import user_name, take_coins, user_in_chat
from bot.modules.dinosaur import Dino, create_dino_connection
from bot.const import GAME_SETTINGS as GS
from bot.modules.item import counts_items

events = mongo_client.tasks.events

@bot.message_handler(text='commands_name.dino_tavern.events', is_authorized=True)
async def events_c(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
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

@bot.message_handler(text='commands_name.dino_tavern.daily_award', is_authorized=True)
async def bonus(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    award_data = GS['daily_award']
    lvl1 = counts_items(award_data['lvl1']['items'], lang) \
        + f', ' + str(award_data['lvl1']['coins']) + ' 👑'

    lvl2 = counts_items(award_data['lvl2']['items'], lang) \
        + f', ' + str(award_data['lvl2']['coins']) + ' 👑'

    bonus = counts_items(award_data['bonus']['items'], lang) \
        + f', ' + str(award_data['bonus']['coins']) + ' 👑'

    text = t('daily_award.info', lang, lvl_1=lvl1, lvl_2=lvl2, bonus=bonus
             )
    
    res = await user_in_chat(userid, -1001673242031)
    print(res)
    
    await bot.send_message(chatid, text, parse_mode='Markdown')
    