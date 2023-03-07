from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.dinosaur import (Dino, check_accessory, downgrade_accessory,
                                  start_sleep)
from bot.modules.localization import t, get_data
from bot.modules.markup import list_to_keyboard, markups_menu as m
from bot.modules.user import User
from bot.modules.states import ChooseOptionState, ChooseIntState

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs


@bot.message_handler(textstart='commands_name.actions.dino_button')
async def edit_dino_buttom(message: Message):
    user_id = message.from_user.id
    user = User(user_id)
    dinos = user.get_dinos()
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
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    dino = transmitted_data['last_dino']

    start_sleep(dino._id, 'short', number * 60)
    await bot.send_message(chatid, 
                t('put_to_bed.sleep', lang),
                reply_markup=m(userid, 'last_menu', lang, True)
                )

async def long_sleep(dino: Dino, userid: int, lang: str):
    start_sleep(dino._id, 'long')
    await bot.send_message(userid, 
                t('put_to_bed.sleep', lang),
                reply_markup=m(userid, 'last_menu', lang, True)
                )

async def end_choice(option: str, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    last_dino = transmitted_data['last_dino']
    
    if option == 'short':
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
                if check_accessory(last_dino, '16'):
                    await long_sleep(last_dino, userid, lang)
                else:
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
                    
                    await ChooseOptionState(end_choice, userid, chatid, lang, options, trans_data)
                    await bot.send_message(userid, 
                            t('put_to_bed.choice', lang), 
                            reply_markup=buttons)
        else:
            await bot.send_message(userid, t('put_to_bed.alredy_busy', lang),
                reply_markup=m(userid, 'last_menu', lang))
    else:
        await bot.send_message(userid, t('edit_dino_button.notfouned', lang),
                reply_markup=m(userid, 'last_menu', lang))
        
        



