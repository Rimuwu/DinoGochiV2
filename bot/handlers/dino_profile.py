from telebot import types
from telebot.asyncio_handler_backends import State, StatesGroup

from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.data_format import chunks, list_to_keyboard, near_key_number
from bot.modules.dinosaur import Dino, Egg
from bot.modules.events import get_one_event
from bot.modules.localization import get_data, t
from bot.modules.markup import get_answer_keyboard
from bot.modules.markup import markups_menu as m
from bot.modules.user import User
from bot.modules.states import DinoStates


async def dino_profile(userid: int, dino: Dino, lang: str):
    text = ''

    text_rare = get_data('rare', lang)
    replics = get_data('p_profile.replics', lang)
    status_rep = t(f'p_profile.stats.{dino.status}', lang)

    season = get_one_event("time_year")
    tem = GAME_SETTINGS['events']['time_year'][season]

    qual = text_rare[dino.quality][0]
    stats_text = ''

    for i in ['heal', 'eat', 'game', 'mood', 'energy']:
        repl = near_key_number(dino.stats[i], replics[i])
        stats_text += f'{tem[i]} {repl} \[ *{dino.stats[i]}%* ]\n'

    text = t('p_profile.profile_text', lang,
             em_name=tem['name'], dino_name=dino.name,
             em_status=tem['status'], status=status_rep,
             em_rare=tem['rare'], qual=qual,
             stats=stats_text
             )

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

    # act_ii = []
    # for itmk in dino.activ_items.keys():
    #     itm = dino.activ_items[itmk]

    #     if itm == None:
    #         act_ii.append(t(f'p_profile.no_item', lang))

    #     else:
    #         item = Functions.item_name(str(itm['item_id']), bd_user['language_code'])

    #         if 'abilities' in itm.keys() and 'endurance' in itm['abilities'].keys():
    #             act_ii.append(f"{item} \[ *{itm['abilities']['endurance']}* ]")
    #         else:
    #             act_ii.append(f'{item}')

    # game, coll, jour, sleep = act_ii
    # text += "\n\n" + text_dict['accs'].format(
    #         game=game, coll=coll, jour=jour, sleep=sleep,
    #         em_game=tem['ac_game'], em_coll=tem['ac_collecting'], em_jour=tem['ac_journey'], 
    #         em_sleep=tem['ac_sleep']
    # )

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
            type='photo', media=dino.image(), parse_mode='Markdown', caption=text)
        )

async def egg_profile(userid: int, egg: Egg, lang: str):
    text = t('p_profile.incubation_text', lang, time_end=egg.remaining_incubation_time())
    img = egg.image()

    await bot.send_photo(userid, img, text, reply_markup=m(userid, 'last_menu', language_code=lang))


@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def dino_handler(message: types.Message):
    user = User(message.from_user.id)
    lang = message.from_user.language_code
    elements = user.get_dinos() + user.get_eggs()

    ret_data = get_answer_keyboard(elements, lang)

    if ret_data['case'] == 0:
        await bot.send_message(user.userid, 
            t('p_profile.no_dinos_eggs'), lang)

    elif ret_data['case'] == 1:
        element = ret_data['element']

        if type(element) == Dino:
            await dino_profile(user.userid, element, lang)
        elif type(element) == Egg:
            await egg_profile(user.userid, element, lang)

    elif ret_data['case'] == 2:# Несколько динозавров / яиц
        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, DinoStates.choose_dino, message.chat.id)
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['dino_answer'] = ret_data['data_names']

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=ret_data['keyboard'])

@bot.message_handler(state=DinoStates.choose_dino, is_authorized=True)
async def answer_dino(message: types.Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    async with bot.retrieve_data(userid, message.chat.id) as data:
        data_names = data['dino_answer']
    await bot.delete_state(userid, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)

    element = data_names[message.text]
    if type(element) == Dino:
        await dino_profile(userid, element, lang)
    elif type(element) == Egg:
        await egg_profile(userid, element, lang)
