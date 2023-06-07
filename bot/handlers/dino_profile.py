from time import time

from telebot import types
from telebot.types import Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.data_format import near_key_number, seconds_to_str
from bot.modules.dinosaur import Dino, Egg
from bot.modules.events import get_one_event
from bot.modules.inline import dino_profile_markup
from bot.modules.item import get_name
from bot.modules.accessory import check_accessory
from bot.modules.localization import get_data, t
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import ChooseDinoState
from bot.modules.user import User

users = mongo_client.bot.users
collecting_task = mongo_client.tasks.collecting
game_task = mongo_client.tasks.game
dino_mood = mongo_client.connections.dino_mood
dinosaurs = mongo_client.bot.dinosaurs

async def dino_profile(userid: int, dino: Dino, lang: str, custom_url: str):
    text = ''

    text_rare = get_data('rare', lang)
    replics = get_data('p_profile.replics', lang)
    status_rep = t(f'p_profile.stats.{dino.status}', lang)
    user = User(userid)

    season = get_one_event('time_year')
    tem = GAME_SETTINGS['events']['time_year'][season]

    stats_text = ''
    # Генерация блока со статистикой
    for i in ['heal', 'eat', 'game', 'mood', 'energy']:
        repl = near_key_number(dino.stats[i], replics[i])
        stats_text += f'{tem[i]} {repl} \[ *{dino.stats[i]}%* ]\n'
    
    if dino.age.days == 0:
        age = seconds_to_str(dino.age.seconds, lang)
    else: age = seconds_to_str(dino.age.days * 86400, lang)
    
    kwargs = {
        'em_name': tem['name'], 'dino_name': dino.name,
        'em_status': tem['status'], 'status': status_rep,
        'em_rare': tem['rare'], 'qual': text_rare[dino.quality][1],
        'em_age': tem['age'], 'age': age
    }
    text = t('p_profile.profile_text', lang, formating=False).format(**kwargs)

    if dino.status == 'journey':
        # w_t = bd_dino['journey_time'] - time.time()
        # jtime = Functions.time_end(w_t, text_dict['journey_time']['set'])

        # text += "\n\n" + tem['activ_journey']
        # text += text_dict['journey_time']['text'].format(jtime=jtime)
        pass

    if dino.status == 'game':
        data = game_task.find_one({'dino_id': dino._id})
        text += t(
                f'p_profile.game.text', lang, em_game_act=tem['em_game_act'])
        if data:
            if True or check_accessory(dino, '4', True):
                end = seconds_to_str(data['game_end'] - int(time()), lang)
                text += t(
                    f'p_profile.game.game_end', lang, end=end)

            duration = seconds_to_str(int(time()) - data['game_start'], lang)
            text += t(
                f'p_profile.game.game_duration', lang, duration=duration)
    
    if dino.status == 'collecting':
        data = collecting_task.find_one({'dino_id': dino._id})
        if data:
            text += t(
                f'p_profile.collecting.text', lang, em_coll_act=tem['em_coll_act'])
            text += t(
                f'p_profile.collecting.progress.{data["collecting_type"]}', lang,
                now = data['now_count'], max_count=data['max_count'])
            
    text += '\n\n' + stats_text
    # Генерация блока с аксессуарами
    add_blok = False
    acsess = {
        'em_game': tem['ac_game'], 'em_coll': tem['ac_collecting'],
        'em_jour': tem['ac_journey'], 'em_sleep': tem['ac_sleep']
    }
    for key, item in dino.activ_items.items():
        if not item:
           acsess[key] = t(f'p_profile.no_item', lang)
        else:
            add_blok = True
            name = get_name(item['item_id'], lang)
            if 'abilities' in item.keys() and 'endurance' in item['abilities'].keys():
               acsess[key] = f'{name} \[ *{item["abilities"]["endurance"]}* ]'
            else: acsess[key] = f'{name}'
                
    menu = dino_profile_markup(add_blok, lang, dino.alt_id)
    if add_blok:
        text += t('p_profile.accs', lang, formating=False).format(**acsess)
    
    # затычка на случай если не сгенерируется изображение
    generate_image = open(f'images/remain/no_generate.png', 'rb')
    msg = await bot.send_photo(userid, generate_image, text,
                parse_mode='Markdown', reply_markup=menu)

    await bot.send_message(userid, t('p_profile.return', lang), 
                reply_markup=m(userid, 'last_menu', lang))
    
    # изменение сообщения с уже нужным изображением
    image = dino.image(user.settings['profile_view'], custom_url)
    await bot.edit_message_media(
        chat_id=userid,
        message_id=msg.id,
        media=types.InputMedia(
            type='photo', media=image, 
            parse_mode='Markdown', caption=text),
        reply_markup=menu
        )

async def egg_profile(userid: int, egg: Egg, lang: str):
    text = t('p_profile.incubation_text', lang, 
             time_end=seconds_to_str(
        egg.remaining_incubation_time(), lang)
        )
    img = egg.image(lang)
    await bot.send_photo(userid, img, text, 
                         reply_markup=m(userid, 'last_menu', language_code=lang))

async def transition(element, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    user = User(userid)
    custom_url = ''
 
    if user and user.premium and 'custom_url' in user.settings:
        custom_url = user.settings['custom_url']
    
    if type(element) == Dino:
        await dino_profile(userid, element, lang, custom_url)
    elif type(element) == Egg:
        await egg_profile(userid, element, lang)

@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def dino_handler(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await ChooseDinoState(transition, userid, message.chat.id, lang) 

@bot.callback_query_handler(func=lambda call: call.data.startswith('dino_profile'), 
                            nothing_state=True)
async def answer_edit(call: types.CallbackQuery):
    dino_data = call.data.split()[1]

    userid = call.from_user.id
    lang = call.from_user.language_code
    trans_data = {
        'userid': userid,
        'lang': lang
    }
    dino = Dino(dino_data) #type: ignore
    await transition(dino, trans_data)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('dino_menu'))
async def dino_menu(call: types.CallbackQuery):
    split_d = call.data.split()
    action = split_d[1]
    alt_key = split_d[2]

    userid = call.from_user.id
    lang = call.from_user.language_code

    dino = dinosaurs.find_one({'alt_id': alt_key})
    if dino:

        if action == 'reset_activ_item':
            ...
        elif action == 'mood_log':
            mood_list = list(dino_mood.find({'dino_id': dino['_id']}))
            mood_dict, text, event_text = {}, '', ''
            res, event_end = 0, 0
            
            for mood in mood_list:
                if mood['type'] not in ['breakdown', 'inspiration']:
                
                    key = mood['action']
                    if key not in mood_dict:
                        mood_dict[key] = {'col': 1, 'unit': mood['unit']}
                    else:
                        mood_dict[key]['col'] += 1
                    res += mood['unit']

                else:
                    event_text = t(f'mood_log.{mood["type"]}.{mood["action"]}', lang)
                    event_end = mood['end_time'] -mood['start_time'] 

            text = t('mood_log.info', lang, result=res)
            if event_text: 
                event_time = seconds_to_str(event_end, lang, True)
                text += t('mood_log.event_info', lang, action=event_text, event_time=event_time)

            text += '\n'

            for key, data_m in mood_dict.items():
                em = '💚'
                if data_m['unit'] <= 0: em = '💔'
                act = t(f'mood_log.{key}', lang)
                
                unit = str(data_m['unit'] * data_m['col'])
                if data_m['unit'] > 0: unit = '+'+unit

                text += f'{em} {act}: `{unit}` '
                if data_m['col'] > 1: text += f'x{data_m["col"]}'
                text += '\n'
    
            await bot.send_message(userid, text, parse_mode='Markdown')