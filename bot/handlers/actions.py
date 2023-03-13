from random import randint
from time import time

from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline, seconds_to_str
from bot.modules.dinosaur import (Dino, check_accessory, edited_stats,
                                  end_sleep, start_sleep)
from bot.modules.localization import get_data, t
from bot.modules.markup import list_to_keyboard
from bot.modules.markup import markups_menu as m
from bot.modules.states import ChooseIntState, ChooseOptionState
from bot.modules.user import User

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs
sleep_task = mongo_client.tasks.sleep


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
async def answer_edit(call: CallbackQuery):
    """ Изменение последнего динозавра (кнопка)
    """
    user_id = call.from_user.id
    lang = call.from_user.language_code
    user = User(user_id)

    message = call.message
    data = call.data.split()[1]

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
