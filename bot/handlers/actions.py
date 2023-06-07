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
                                      ChoosePagesState, ChooseStepState)
from bot.modules.user import User, count_inventory_items, premium
from bot.modules.friend_tools import start_friend_menu

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
    dinos = user.get_dinos
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
                reply_markup=m(user_id, 'actions_menu', lang, True)
                              )
        
async def short_sleep(number: int, transmitted_data: dict):
    """ Отправляем в которкий сон
    """
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    dino = transmitted_data['last_dino']

    check_accessory(dino, '16', True)
    start_sleep(dino._id, 'short', number * 60)
    await bot.send_message(chatid, 
                t('put_to_bed.sleep', lang),
                reply_markup=m(userid, 'last_menu', lang, True)
                )

async def long_sleep(dino: Dino, userid: int, lang: str):
    """ Отправляем дино в длинный сон
    """
    start_sleep(dino._id, 'long')
    await bot.send_message(userid, 
                t('put_to_bed.sleep', lang),
                reply_markup=m(userid, 'last_menu', lang, True)
                )

async def end_choice(option: str, transmitted_data: dict):
    """Функция обработки выбора варианта (длинный или короткий сон)
    """
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    last_dino = transmitted_data['last_dino']
    
    if last_dino.status == 'pass':
        if option == 'short':
            # Если короткий, то спрашиваем сколько дино должен спать
            cancel_button = t('buttons_name.cancel', lang)
            buttons = list_to_keyboard([cancel_button])
            await ChooseIntState(short_sleep, userid, 
                                chatid, lang, min_int=5, max_int=480)

            await bot.send_message(userid, 
                                t('put_to_bed.choice_time', lang), 
                                reply_markup=buttons)
        
        elif option == 'long':
            await long_sleep(last_dino, userid, lang)
    
    else:
        await bot.send_message(userid, t('put_to_bed.alredy_busy', lang),
            reply_markup=
                                inline_menu('dino_profile', lang, 
                                            dino_alt_id_markup=last_dino.alt_id
                                                            ))

@bot.message_handler(text='commands_name.actions.put_to_bed')
async def put_to_bed(message: Message):
    """Уложить спать динозавра
    """
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    user = User(userid)
    last_dino = user.get_last_dino()

    if last_dino:
        if last_dino.status == 'pass':
            if last_dino.stats['energy'] >= 90:
                await bot.send_message(message.chat.id, 
                                       t('put_to_bed.dont_want', lang)
                                       )
            
            else:
                if not check_accessory(last_dino, '16'):
                    # Если нет мишки, то просто длинный сон
                    await long_sleep(last_dino, userid, lang)
                else:
                    # Даём выбор сна
                    sl_buttons = get_data('put_to_bed.buttons', lang).copy()
                    cancel_button = t('buttons_name.cancel', lang)
                    sl_buttons.append(cancel_button)

                    buttons = list_to_keyboard(sl_buttons, 2, one_time_keyboard=True)
                    options = {
                        sl_buttons[0][0]: 'long',
                        sl_buttons[0][1]: 'short'
                    }
                    trans_data = { 
                        'last_dino': last_dino
                    }
                    
                    await ChooseOptionState(end_choice, userid, chatid, lang, options, trans_data) # Ожидаем выбор варианта
                    await bot.send_message(userid, 
                            t('put_to_bed.choice', lang), 
                            reply_markup=buttons)
        else:
            await bot.send_message(userid, t('put_to_bed.alredy_busy', lang),
                reply_markup=
                                inline_menu('dino_profile', lang, 
                                            dino_alt_id_markup=last_dino.alt_id
                                                            ))
    else:
        await bot.send_message(userid, t('edit_dino_button.notfouned', lang),
                reply_markup=m(userid, 'last_menu', lang))

@bot.message_handler(text='commands_name.actions.awaken')
async def awaken(message: Message):
    """Пробуждение динозавра
    """
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    user = User(userid)
    last_dino = user.get_last_dino()

    if last_dino:
        if last_dino.status == 'sleep':
            sleeper = sleep_task.find_one({'dino_id': last_dino._id})
            if sleeper:
                if sleeper['sleep_type'] == 'long':
                    sleep_time = int(time()) - sleeper['sleep_start']
                    healthy_sleep = 6 * 3600 # Время здорового сна

                    if sleep_time >= healthy_sleep \
                        or last_dino.stats['energy'] == 100:

                        await end_sleep(last_dino._id, sleeper['_id'], sleep_time)
                    else:
                        # Если динозавр в долгом сне проспал меньше 6-ми часов, то штраф
                        add_mood(last_dino._id, 'bad_sleep', -1, 10800)
                        await end_sleep(last_dino._id, sleeper['_id'], send_notif=False)
                        
                        await bot.send_message(chatid, 
                                               t('awaken.down_mood', lang, 
                                                 time_end=seconds_to_str(sleep_time, lang)
                                                ),
                                               reply_markup=m(userid, 'last_menu', lang))
                    
                elif sleeper['sleep_type'] == 'short':
                    sleep_time = sleeper['sleep_end'] - sleeper['sleep_start']
                    await end_sleep(last_dino._id, sleeper['_id'], sleep_time)
            else:
                last_dino.update({'$set': {'status': 'pass'}})
                await bot.send_message(chatid, t('awaken.not_sleep', lang),
                reply_markup=m(userid, 'last_menu', lang))

        else:
            await bot.send_message(chatid, t('awaken.not_sleep', lang),
                reply_markup=m(userid, 'last_menu', lang))
    else:
        await bot.send_message(chatid, t('edit_dino_button.notfouned', lang),
                reply_markup=m(userid, 'last_menu', lang))
        
async def adapter_function(return_dict, transmitted_data):
    count = return_dict['count']
    item = transmitted_data['item']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    dino = transmitted_data['dino']
    lang = transmitted_data['lang']
    
    send_status, return_text = await use_item(userid, chatid, lang, item, count, dino)
    
    if send_status:
        await bot.send_message(chatid, return_text, parse_mode='Markdown', reply_markup=m(userid, 'last_menu', lang))
        
async def inventory_adapter(item, transmitted_data):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    dino: Dino = transmitted_data['dino']

    transmitted_data['item'] = item
    
    limiter = 100 # Ограничение по количеству использований за раз
    item_data = get_item_data(item['item_id'])
    item_name = get_name(item['item_id'], lang)
    
    base_item = items.find_one({'owner_id': userid, 'items_data': item})
    if base_item:
        if 'abilities' in item.keys() and 'uses' in item['abilities']:
            max_count = base_item['count'] * base_item['items_data']['abilities']['uses']
        else: max_count = base_item['count']

        if max_count > limiter: max_count = limiter
        
        percent = 1
        if dino.age.days >= 10:
            percent, repeat = dino.memory_percent('games', item['item_id'], False)

        steps = [
            {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
             "translate_message": True,
                'message': {'text': 'css.wait_count', 
                            'reply_markup': feed_count_markup(
                                dino.stats['eat'], int(item_data['act'] * percent), max_count, item_name, lang)}}
                ]
        await ChooseStepState(adapter_function, userid, chatid, 
                                  lang, steps, 
                              transmitted_data=transmitted_data)

@bot.message_handler(text='commands_name.actions.feed')
async def feed(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    user = User(userid)
    
    transmitted_data = {
        'chatid': chatid,
        'lang': lang,
        'dino': user.get_last_dino()
    }
    
    await start_inv(inventory_adapter, userid, chatid, lang, ['eat'], changing_filters=False, transmitted_data=transmitted_data)

async def start_game_ent(userid: int, chatid: int, 
                         lang: str, dino: Dino, 
                         friend: int = 0, join: bool = True):
    """ Запуск активности игра
        friend - id друга при наличии
        join - присоединяется ли человек к игре
    """
    transmitted_data = {
        'dino': dino, 
        'friend': friend, 'join': join
    }

    # Создание первого выбора
    game_data = get_data('entertainments', lang)
    game_buttons, options = [], {}
    last_game = '-'
    need = ['console', 'snake', 'pin-pong', 'ball']

    if check_accessory(dino, '44'):
        need += ["puzzles", "chess", "jenga", "dnd"]

    if premium(userid):
        need += ["monopolia", "bowling", "darts", "golf"]

    for key, value in game_data['game'].items():
        if key in need:
            options[value] = key
            game_buttons.append(value)

    if dino.memory['games']:
        last = dino.memory['games'][0]
        last_game = t(f'entertainments.game.{last}', lang)

    # Второе сообщение
    buttons = {}

    for key, value in get_data('entertainments.time', lang).items():
        buttons[value['text']] = f'chooseinline {key}'
    markup = list_to_inline([buttons])

    steps = [
        {"type": 'pages', "name": 'game', 
          "data": {"options": options}, 
          'translate_message': True,
          'translate_args': {'last_game': last_game},
          'message': {'text': 'entertainments.answer_game'
              }
        },
        {
            "type": 'update_data', 'name': 'zero',
            'function': delete_markup,
            'async': True
        },
        {"type": 'inline', "name": 'time', "data": {}, 
          'translate_message': True,
          'delete_message': True,
          'message': {'text': 'entertainments.answer_text',
                      'reply_markup': markup
              }
        }
    ]

    await ChooseStepState(game_start, userid, chatid, lang, steps, transmitted_data)

async def delete_markup(transmitted_data):
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']

    await bot.send_message(chatid, '➡️', reply_markup=cancel_markup(lang))
    return transmitted_data, 0

async def game_start(return_data: dict, 
                     transmitted_data: dict):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    dino: Dino = transmitted_data['dino']

    friend = transmitted_data['friend']
    join_status = transmitted_data['join']

    game = return_data['game']
    code = return_data['time']
    
    if dino.status == 'pass':
        percent, repeat = dino.memory_percent('games', game)

        r_t = get_data('entertainments', lang)['time'][code]['data']
        game_time = randint(*r_t) * 60

        res = check_inspiration(dino._id, 'game')
        if res: percent += 1.0

        dino.game(game_time, percent)
        image = dino_game(dino.data_id)

        text = t(f'entertainments.game_text.m{str(repeat)}', lang, 
                game=t(f'entertainments.game.{game}', lang)) + '\n'
        if percent < 1.0:
            text += t(f'entertainments.game_text.penalty', lang, percent=int(percent*100))

        await bot.send_photo(chatid, image, text, reply_markup=m(userid, 'last_menu', lang, True))

        # Пригласить друга
        if friend and not join_status:
            await send_action_invite(userid, friend, 'game', dino.alt_id, lang)
        elif friend and join_status:
            ...
        else:
            text = t('entertainments.invite_friend.text', lang)
            button = t('entertainments.invite_friend.button', lang)
            markup = list_to_inline([
                {button: f'invite_to_action game {dino.alt_id}'}
            ])
            await bot.send_message(chatid, text, reply_markup=markup)

@bot.message_handler(text='commands_name.actions.entertainments')
async def entertainments(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    user = User(userid)
    dino = user.get_last_dino()
    if dino:
        await start_game_ent(userid, chatid, lang, dino)

@bot.message_handler(text='commands_name.actions.stop_game')
async def stop_game(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    
    user = User(userid)
    last_dino = user.get_last_dino()
    if last_dino:
        penalties = GAME_SETTINGS['penalties']["games"]
        game_data = game_task.find_one({'dino_id': last_dino._id})
        random_tear, text = 1, ''

        res = check_breakdown(last_dino._id, 'unrestrained_play')

        if not res:
            if game_data:
                # Определение будет ли дебафф к настроению
                if game_data['game_percent'] == penalties['0']:
                    random_tear = randint(1, 2)
                elif game_data['game_percent'] == penalties['1']:
                    random_tear = randint(1, 3)
                elif game_data['game_percent'] == penalties['2']:
                    random_tear = randint(0, 2)
                elif game_data['game_percent'] == penalties['3']:
                    random_tear = 0

                if randint(1, 2) == 1 or not random_tear:
                    
                    if random_tear == 1:
                        # Дебафф к настроению
                        text = t('stop_game.like', lang)
                        add_mood(last_dino._id, 'stop_game', randint(-2, -1), 3600)
                    elif random_tear == 0:
                        # Не нравится динозавру играть, без дебаффа
                        text = t('stop_game.dislike', lang)
                    else:
                        # Завершение без дебаффа
                        text = t('stop_game.whatever', lang)

                    await end_game(last_dino._id, False)
                else:
                    # Невозможно оторвать от игры
                    text = t('stop_game.dont_tear', lang)

                await bot.send_message(chatid, text, reply_markup=m(userid, 'last_menu', lang, True))
                
            else:
                if last_dino.status == 'game':
                    last_dino.update({'$set': {'status': 'pass'}})
                
                await bot.send_message(chatid, '❌', reply_markup=m(userid, 'last_menu', lang, True))


async def collecting_adapter(return_data, transmitted_data):
    dino = transmitted_data['dino'] # type: Dino
    count = return_data['count']
    option = return_data['option']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    
    eat_count = count_inventory_items(userid, ['eat'])
    st_premium = premium(userid)
    
    if st_premium and eat_count + count > GAME_SETTINGS['premium_max_eat_items'] \
        or not st_premium and eat_count + count > GAME_SETTINGS['max_eat_items']:
            
        text = t(f'collecting.max_count', lang,
                eat_count=eat_count)
        await bot.send_message(chatid, text, reply_markup=m(
            userid, 'last_menu', lang))
    else:
        dino.collecting(userid, option, count)
        
        image = dino_collecting(dino.data_id, option)
        text = t(f'collecting.result.{option}', lang,
                dino_name=dino.name, count=count)
        stop_button = t(f'collecting.stop_button.{option}', lang)
        markup = list_to_inline([
            {stop_button: f'collecting stop {dino.alt_id}'}])
        
        await bot.send_photo(chatid, image, text, reply_markup=markup)
        await bot.send_message(chatid, t('back_text.actions_menu', lang),
                                    reply_markup=m(userid, 'last_menu', lang)
                                    )


@bot.message_handler(text='commands_name.actions.collecting')
async def collecting_button(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    user = User(userid)
    last_dino = user.get_last_dino()
    
    if last_dino:
        if last_dino.status == 'pass':
            if user.premium:
                max_count = GAME_SETTINGS['premium_max_collecting']
            else: max_count = GAME_SETTINGS['max_collecting']
            
            data_options = get_data('collecting.buttons', lang)
            options = dict(zip(data_options.values(), data_options.keys()))
            markup = list_to_keyboard([list(data_options.values()), 
                                    [t('buttons_name.cancel', lang)]], 2)
            
            steps = [
                {"type": 'option', "name": 'option', 
                 "data": {"options": options}, 
                 "translate_message": True,
                    'message': {'text': 'collecting.way', 
                    'reply_markup': markup}
                    },
                {"type": 'int', "name": 'count', 
                 "data": {"max_int": max_count}, 
                 "translate_message": True,
                    'message': {'text': 'collecting.wait_count', 
                    'reply_markup': count_markup(max_count)}
                    }
                        ]
            await ChooseStepState(collecting_adapter, userid, chatid, 
                                        lang, steps, 
                                    transmitted_data={'dino': last_dino, 'delete_steps': True})
    
        else:
            await bot.send_message(chatid, t('collecting.alredy_busy', lang),
                                reply_markup=
                                inline_menu('dino_profile', lang, 
                                            dino_alt_id_markup=last_dino.alt_id)
                                )
            
@bot.message_handler(text='commands_name.actions.progress')
async def collecting_progress(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    
    user = User(userid)
    last_dino = user.get_last_dino()
    if last_dino:
        
        data = collecting_task.find_one({'dino_id': last_dino._id})
        if data:
            stop_button = t(
                f'collecting.stop_button.{data["collecting_type"]}', lang)

            image = open(f'images/actions/collecting/{data["collecting_type"]}.png', 'rb')
            text = t(f'collecting.progress.{data["collecting_type"]}', lang,
                    now = data['now_count'], max_count=data['max_count']
                    )
            
            await bot.send_photo(chatid, image, text, 
                                 reply_markup=list_to_inline(
                                  [{stop_button: f'collecting stop {last_dino.alt_id}'}]
                                     ))
        else:
            await bot.send_message(chatid, '❌',
                                    reply_markup=m(userid, 'last_menu', lang)
                                    )
    

@bot.callback_query_handler(func=
                            lambda call: call.data.startswith('collecting'), is_authorized=True)
async def collecting_callback(callback: CallbackQuery):
    dino_data = callback.data.split()[2]
    action = callback.data.split()[1]
    
    lang = callback.from_user.language_code
    
    dino = Dino(dino_data) #type: ignore
    data = collecting_task.find_one({'dino_id': dino._id})
    if data and dino:
        items_list = []
        for key, count in data['items'].items():
            items_list += [key] * count
            
        items_names = counts_items(items_list, lang)
            
        if action == 'stop':
            await end_collecting(dino._id, 
                                 data['items'], data['sended'], 
                                 items_names)

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

    # Выбор друга и функция send_action_invite
    await start_friend_menu(invite_adp, userid, chatid, lang, True, transmitted_data)

    text = t('invite_to_action', lang)
    await bot.send_message(chatid, text, parse_mode='Markdown')

@bot.callback_query_handler(func=
                            lambda call: call.data.startswith('join_to_action'))
async def join(callback: CallbackQuery):
    lang = callback.from_user.language_code
    chatid = callback.message.chat.id
    data = callback.data.split()
    
    сюда
    
    # Выбор динозавра и присоединение к активности, отсылать фотку так же и к кому присоединились
    # + 0.5 к эффективности и настроение "поиграл с другом"