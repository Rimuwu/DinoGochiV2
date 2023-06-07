
from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.dinosaur import Dino
from bot.modules.images import dino_journey
from bot.modules.localization import get_data, t
from bot.modules.states_tools import ChooseStepState
from bot.modules.user import User

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs


async def journey_start_adp(return_data: dict, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    dino: Dino = transmitted_data['last_dino']
    friend = transmitted_data['friend']
    location = return_data['location']
    time_key = return_data['time_key']
    
    image = dino_journey(dino.data_id, location, friend)
    
    print(return_data)
    print(transmitted_data)

async def start_journey(userid: int, chatid: int, lang: str, 
                        friend: int = 0):
    user = User(userid)
    last_dino = user.get_last_dino()

    premium_loc = ['magic-forest']
    content_data = get_data('journey_start', lang)

    text, a = content_data['ask_loc'], 1
    buttons = {}

    for key, dct in content_data['locations'].items():
        text += f"*{a}*. {dct['text']}\n\n"
        if user.premium or key not in premium_loc:
            buttons[dct['name']] = f'chooseinline {key}'
        a += 1

    text_complexity, buttons_complexity = '', []
    comp = content_data['complexity']
    text_complexity = comp['text']
    buttons_complexity.append({comp['button']: 'journey_complexity'})

    m1_reply = list_to_inline(buttons_complexity)
    m2_reply = list_to_inline([buttons], 2)

    await bot.send_message(chatid, text_complexity, 
                           reply_markup=m1_reply)

    text_time = content_data['time_info']
    buttons_time = [{}, {}, {}]
    b = 2
    for key, dct in content_data['time_text'].items():
        if len(buttons_time[2 - b].keys()) >= b + 1: b -= 1
        buttons_time[2 - b][dct['text']] = f'chooseinline {key}'

    m3_reply = list_to_inline(buttons_time)

    steps = [
        {"type": 'inline', "name": 'location', "data": {}, 
         "image": 'images/actions/journey/preview.png',
         "message": {"caption": text, "reply_markup": m2_reply}
        },
        {"type": 'inline', "name": 'time_key', "data": {}, 
         "message": {"caption": text_time, "reply_markup": m3_reply}
        }
    ]

    await ChooseStepState(journey_start_adp, userid, chatid, lang, steps, 
                          {'last_dino': last_dino, "edit_message": True, 'friend': friend})

@bot.message_handler(text='commands_name.actions.journey')
async def journey_com(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    await start_journey(userid, chatid, lang)

@bot.callback_query_handler(func=
                            lambda call: call.data.startswith('journey_complexity'))
async def journey_complexity(callback: CallbackQuery):
    lang = callback.from_user.language_code
    chatid = callback.message.chat.id
    
    text = t('journey_complexity', lang)
    await bot.send_message(chatid, text, parse_mode='Markdown')
