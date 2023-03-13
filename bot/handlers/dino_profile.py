from telebot import types
from telebot.types import Message

from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.data_format import near_key_number, seconds_to_str
from bot.modules.dinosaur import Dino, Egg
from bot.modules.events import get_one_event
from bot.modules.item import get_name
from bot.modules.localization import get_data, t
from bot.modules.markup import markups_menu as m
from bot.modules.states import ChooseDinoState
from bot.modules.user import User


async def dino_profile(userid: int, dino: Dino, lang: str):
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
    
    kwargs = {
        'em_name': tem['name'], 'dino_name': dino.name,
        'em_status': tem['status'], 'status': status_rep,
        'em_rare': tem['rare'], 'qual': text_rare[dino.quality][0],

        'stats': stats_text
    }
    text = t('p_profile.profile_text', lang, formating=False).format(**kwargs)

    if dino.status == 'journey':
        # w_t = bd_dino['journey_time'] - time.time()
        # jtime = Functions.time_end(w_t, text_dict['journey_time']['set'])

        # text += "\n\n" + tem['activ_journey']
        # text += text_dict['journey_time']['text'].format(jtime=jtime)
        pass

    if dino.status == 'game':
        # if Functions.acc_check(bot, bd_user, '4', dino_user_id, True):
        #     w_t = bd_dino['game_time'] - time.time()
        #     gtime = Functions.time_end(w_t, text_dict['game_time']['set'])

        #     text += "\n\n" + tem['activ_game']
        #     text += text_dict['game_time']['text'].format(gtime=gtime)
        pass
    
    if dino.status == 'hunting':
        # targ = bd_dino['target']
        # number, tnumber = targ[0], targ[1]
        # prog = int(number / (tnumber / 100))

        # text += "\n\n" + tem['activ_hunting']
        # text += text_dict['collecting_progress'].format(progress=prog)
        pass

    # Генерация блока с аксессуарами
    acsess = {
        'em_game': tem['ac_game'], 'em_coll': tem['ac_collecting'],
        'em_jour': tem['ac_journey'], 'em_sleep': tem['ac_sleep']
    }
    for key, item in dino.activ_items.items():
        if not item:
           acsess[key] = t(f'p_profile.no_item', lang)
        else:
            name = get_name(item['item_id'], lang)
            if 'abilities' in item.keys() and 'endurance' in item['abilities'].keys():
               acsess[key] = f'{name} \[ *{item["abilities"]["endurance"]}* ]'
            else:
                acsess[key] = f'{name}'

    text += t('p_profile.accs', lang, formating=False).format(**acsess)

    # затычка на случай если не сгенерируется изображение
    generate_image = open(f'images/remain/no_generate.png', 'rb')
    msg = await bot.send_photo(userid, generate_image, text,
                parse_mode='Markdown')

    await bot.send_message(userid, t('p_profile.return', lang), 
                reply_markup=m(userid, 'last_menu', lang))
    
    # изменение сообщения с уже нужным изображением
    await bot.edit_message_media(
        chat_id=userid,
        message_id=msg.id,
        media=types.InputMedia(
            type='photo', media=dino.image(user.settings['profile_view']), 
            parse_mode='Markdown', caption=text)
        )

async def egg_profile(userid: int, egg: Egg, lang: str):
    text = t('p_profile.incubation_text', lang, 
             time_end=seconds_to_str(
        egg.remaining_incubation_time(), lang)
        )
    img = egg.image(lang)
    await bot.send_photo(userid, img, text, 
                         reply_markup=m(userid, 'last_menu', language_code=lang))

async def transition(element: Dino | Egg, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']

    if type(element) == Dino:
        await dino_profile(userid, element, lang) #type: ignore
    elif type(element) == Egg:
        await egg_profile(userid, element, lang) #type: ignore

@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def dino_handler(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await ChooseDinoState(transition, userid, message.chat.id, lang) 

@bot.callback_query_handler(func=lambda call: call.data.startswith('dino_profile'))
async def answer_edit(call: types.CallbackQuery):
    data = call.data.split()[1]

    userid = call.from_user.id
    lang = call.from_user.language_code
    trans_data = {
        'userid': userid,
        'lang': lang
    }
    dino = Dino(data) #type: ignore
    await transition(dino, trans_data)