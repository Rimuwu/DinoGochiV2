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
from bot.modules.user import user_name, take_coins
from bot.modules.dinosaur import Dino, create_dino_connection

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
        event_text = t(f"events.{event['_id']}", lang)
        if event['_id'] == 'time_year':
            event_text = event_text[event['data']['season']]
        text += f'+{a}. {event_text}\n'

    await bot.send_message(chatid, text)