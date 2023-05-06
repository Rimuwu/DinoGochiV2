from random import randint
from time import time

from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str)
from bot.modules.dinosaur import Dino, edited_stats, end_sleep, start_sleep
from bot.modules.images import dino_game
from bot.modules.inventory_tools import start_inv
from bot.modules.item import get_data as get_item_data
from bot.modules.item import get_name
from bot.modules.item_tools import check_accessory, use_item
from bot.modules.localization import get_data, t
from bot.modules.markup import count_markup, feed_count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.mood import add_mood
from bot.modules.states_tools import (ChooseIntState, ChooseOptionState,
                                      ChooseStepState)
from bot.modules.user import User

users = mongo_client.bot.users
items = mongo_client.bot.items
dinosaurs = mongo_client.bot.dinosaurs
sleep_task = mongo_client.tasks.sleep
game_task = mongo_client.tasks.game


@bot.message_handler(textstart='commands_name.actions.dino_button')
async def edit_dino_buttom(message: Message):
    """ Изменение последнего динозавра (команда)
    """
    user_id = message.from_user.id
    user = User(user_id)
    dinos = user.get_dinos
    data_names = {}

    for element in dinos:
        txt = f'🦕 {element.name}' #type: ignore
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

@bot.message_handler(textstart='commands_name.actions.put_to_bed')
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
                reply_markup=m(userid, 'last_menu', lang))
    else:
        await bot.send_message(userid, t('edit_dino_button.notfouned', lang),
                reply_markup=m(userid, 'last_menu', lang))

@bot.message_handler(textstart='commands_name.actions.awaken')
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
                    healthy_sleep = 8 * 3600 # Время здорового сна

                    if sleep_time >= healthy_sleep:
                        await end_sleep(last_dino._id, sleeper['_id'], sleep_time)
                    else:
                        # Если динозавр в долгом сне проспал меньше 8-ми часов, то штраф
                        down_mood = randint(-20, 0)
                        mood = edited_stats(last_dino.stats['mood'], down_mood)

                        last_dino.update({"$set": {'stats.mood': mood}})
                        await end_sleep(last_dino._id, sleeper['_id'], send_notif=False)
                        
                        await bot.send_message(chatid, 
                                               t('awaken.down_mood', lang, 
                                                 down_mood=down_mood,
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
    dino = transmitted_data['dino']

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
        
        steps = [
            {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                'message': {'text': t('css.wait_count', lang), 
                            'reply_markup': feed_count_markup(
                                dino.stats['eat'], item_data['act'], max_count, item_name, lang)}}
                ]
        await ChooseStepState(adapter_function, userid, chatid, 
                                  lang, steps, 
                              transmitted_data=transmitted_data)

@bot.message_handler(textstart='commands_name.actions.feed')
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
    
async def entertainments_adapter(game, transmitted_data):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    dino = transmitted_data['dino']
    buttons = {}
    
    for key, value in get_data('entertainments.time', lang).items():
        buttons[value['text']] = f'game_start {key} {dino.alt_id} {game}'
        
    markup = list_to_inline([buttons])
    await bot.send_message(chatid, t('entertainments.answer_text', lang), reply_markup=markup)
    await bot.send_message(chatid, t('entertainments.adapter', lang), reply_markup=m(userid, 'last_menu', lang))

    
@bot.message_handler(textstart='commands_name.actions.entertainments')
async def entertainments(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    user = User(userid)
    last_dino = user.get_last_dino()
    transmitted_data = {'dino': last_dino}
    
    if last_dino:
        if last_dino.status == 'pass':
            game_data = get_data('entertainments', lang)
            game_buttons = []
            options = {}
            need = ['console', 'snake', 'pin-pong', 'ball']
            
            if check_accessory(last_dino, '44'):
                need += ["puzzles", "chess", "jenga", "dnd"]
                
            for key, value in game_data['game'].items(): #type: ignore
                if key in need:
                    options[value] = key
                    game_buttons.append(value)

            markup = list_to_keyboard([game_buttons, t('buttons_name.cancel', lang)])
            
            await ChooseOptionState(entertainments_adapter, userid, chatid, lang, options, transmitted_data=transmitted_data)
            await bot.send_message(chatid, game_data['answer_game'],reply_markup=markup) #type: ignore
        
        else:
            await bot.send_message(chatid, t('entertainments.alredy_busy', lang))

@bot.callback_query_handler(is_authorized=True, 
                            func=lambda call: call.data.startswith('game_start'))
async def game_button(callback: CallbackQuery):
    game = callback.data.split()[3]
    dino_data = callback.data.split()[2]
    code = callback.data.split()[1]
    lang = callback.from_user.language_code
    chatid = callback.message.chat.id
    userid = callback.from_user.id
    dino = Dino(dino_data) #type: ignore
    
    percent, repeat = dino.memory_percent('games', game)
    
    r_t = get_data('entertainments', lang)['time'][code]['data']
    game_time = randint(*r_t) * 60
        
    dino.game(game_time, percent)
    image = dino_game(dino.data_id)
    
    text = t(f'entertainments.game_text.m{str(repeat)}', lang, 
             game=t(f'entertainments.game.{game}', lang)) + '\n'
    if percent < 1.0:
        text += t(f'entertainments.game_text.penalty', lang, percent=percent)

    await bot.send_photo(chatid, image, text, reply_markup=m(userid, 'last_menu', lang, True))

@bot.message_handler(textstart='commands_name.actions.stop_game')
async def stop_game(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    
    user = User(userid)
    last_dino = user.get_last_dino()
    if last_dino:
        penalties = GAME_SETTINGS['penalties']["game"]
        game_data = game_task.find_one({'dino_id': last_dino._id})
        random_tear = 1
        text = ''

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
                    add_mood(last_dino._id, 'end_game', randint(-2, -1), 3600)
                elif random_tear == 0:
                    # Не нравится динозавру играть, без дебаффа
                    text = t('stop_game.dislike', lang)
                else:
                    # Завершение без дебаффа
                    text = t('stop_game.whatever', lang)

                game_task.delete_one({'_id': game_data['_id']})
                last_dino.update({'$set': {'status': 'pass'}})
            else:
                # Невозможно оторвать от игры
                text = t('stop_game.dont_tear', lang)

            await bot.send_message(chatid, text, reply_markup=m(userid, 'last_menu', lang, True))
        else:
            if last_dino.status == 'game':
                last_dino.update({'$set': {'status': 'pass'}})
                
                
async def collecting_adapter(return_data, transmissed_data):
    ...

@bot.message_handler(textstart='commands_name.actions.collecting')
async def collecting(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    user = User(userid)
    last_dino = user.get_last_dino()
    
    data_options = get_data('collecting.buttons', lang)
    options = dict(zip(data_options.values(), data_options.keys()))
    markup = list_to_keyboard([list(data_options.values()), 
                              [t('buttons_name.cancel', lang)]], 2)
    
    steps = [
        {"type": 'option', "name": 'option', "data": {"options": options}, 
            'message': {'text': t('collecting.way', lang), 
            'reply_markup': markup}
            },
        {"type": 'int', "name": 'count', "data": {"max_int": 100}, 
            'message': {'text': t('css.wait_count', lang), 
            'reply_markup': count_markup(100)}
            }
                 ]
    await ChooseStepState(collecting_adapter, userid, chatid, 
                                  lang, steps, 
                              transmitted_data={'dino': last_dino})