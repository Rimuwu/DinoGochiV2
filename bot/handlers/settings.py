from telebot.types import Message, User

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_keyboard, chunks
from bot.modules.localization import t, get_data
from bot.modules.markup import tranlate_data, markups_menu as m
from bot.modules.states import SettingsStates, dino_answer
from bot.modules.dinosaur import Dino

users = mongo_client.bot.users


async def notification(user: User, result: bool):
    text = t(f'not_set.{result}', user.language_code)
    await bot.send_message(user.id, text, 
                    reply_markup=m(user.id, 'last_menu', user.language_code))
    users.update_one({'userid': user.id}, {"$set": {'settings.notifications': result}})

@bot.message_handler(text='commands_name.settings.notification', 
                     is_authorized=True)
async def notification_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    prefix = 'buttons_name.'
    buttons = [
        ['enable', 'disable'],
        ['cancel']
    ]
    translated = tranlate_data(buttons, lang, prefix)
    keyboard = list_to_keyboard(translated, 2)

    await bot.set_state(userid, SettingsStates.settings_choose, 
                        message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['func'] = notification
        data['settings_data'] = {translated[0][0]: True, 
                                 translated[0][1]: False}

    await bot.send_message(userid, t('not_set.info', lang), 
                           reply_markup=keyboard)


async def faq(user, result):
    text = t(f'settings_faq.{result}', user.language_code)
    await bot.send_message(user.id, text, 
                    reply_markup=m(user.id, 'last_menu', user.language_code))
    users.update_one({'userid': user.id}, {"$set": {'settings.faq': result}})

@bot.message_handler(text='commands_name.settings.faq', 
                     is_authorized=True)
async def faq_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    prefix = 'buttons_name.'
    buttons = [
        ['enable', 'disable'],
        ['cancel']
    ]
    translated = tranlate_data(buttons, lang, prefix)
    keyboard = list_to_keyboard(translated, 2)

    await bot.set_state(userid, SettingsStates.settings_choose, 
                        message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['func'] = faq
        data['settings_data'] = {translated[0][0]: True, 
                                 translated[0][1]: False}

    await bot.send_message(userid, t('settings_faq.info', lang), 
                           reply_markup=keyboard)


async def dino_profile(user, result):
    data = get_data('profile_view.ans', user.language_code)
    text = t(f'profile_view.result', user.language_code, res = data[result-1])
    await bot.send_message(user.id, text, 
                    reply_markup=m(user.id, 
                    'last_menu', user.language_code))
    users.update_one({'userid': user.id}, {"$set": {'settings.profile_view': result}})

@bot.message_handler(text='commands_name.settings.dino_profile', 
                     is_authorized=True)
async def dino_profile_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    settings_data, time_list = {}, []

    for i in get_data('profile_view.ans', lang):
        time_list.append(i)
        ind = time_list.index(i) + 1
        settings_data[i] = ind

    buttons = list(chunks(time_list, 2))
    buttons.append([t('buttons_name.cancel', lang)])

    keyboard = list_to_keyboard(buttons, 2)
    await bot.set_state(userid, SettingsStates.settings_choose, 
                        message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['func'] = dino_profile
        data['settings_data'] = settings_data

    await bot.send_message(userid, t('profile_view.info', lang), 
                           reply_markup=keyboard)


async def inventory(user, result):
    text = t(f'inv_set_pages.accept', user.language_code, 
             gr = result[0], vr = result[1]
             )
    await bot.send_message(user.id, text, 
                    reply_markup=m(user.id, 'last_menu', user.language_code))
    users.update_one({'userid': user.id}, {"$set": {'settings.inv_view': result}})

@bot.message_handler(text='commands_name.settings.inventory', 
                     is_authorized=True)
async def inventory_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    settings_data, time_list = {}, []

    for i in get_data('inv_set_pages.ans', lang):
        time_list.append(i)
        settings_data[i] = list(int(strn) for strn in i.split(' | '))

    buttons = list(chunks(time_list, 2))
    buttons.append([t('buttons_name.cancel', lang)])

    keyboard = list_to_keyboard(buttons, 2)
    await bot.set_state(userid, SettingsStates.settings_choose, 
                        message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['func'] = inventory
        data['settings_data'] = settings_data

    await bot.send_message(userid, t('inv_set_pages.info', lang), 
                           reply_markup=keyboard)
    

@bot.message_handler(state=SettingsStates.settings_choose, is_authorized=True)
async def answer_dino(message: Message):
    user = message.from_user

    async with bot.retrieve_data(user.id, message.chat.id) as data:
        settings_data = data['settings_data']
        func = data['func']

    await bot.delete_state(user.id, message.chat.id)
    await bot.reset_data(message.from_user.id, message.chat.id)

    if message.text in settings_data.keys():
        await func(user, settings_data[message.text])
    else:
        await bot.send_message(message.chat.id, "❌", 
                    reply_markup=m(message.from_user.id, 'last_menu', message.from_user.language_code))


async def transition(dino: Dino, data: dict):
    userid = data['userid']
    lang = data['lang']

    text = t('rename_dino.info', lang, last_name=dino.name)
    keyboard = [t('buttons_name.cancel', lang)]
    markup = list_to_keyboard(keyboard, one_time_keyboard=True)

    await bot.set_state(userid, SettingsStates.rename_dino_step_name, 
                        userid)
    async with bot.retrieve_data(userid, userid) as data:
        data['dino'] = dino

    await bot.send_message(userid, text, reply_markup=markup)

@bot.message_handler(text='commands_name.settings.dino_name', 
                     is_authorized=True)
async def rename_dino(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    data = {
        'userid': userid,
        'lang': lang
    }
    await dino_answer(transition, userid, message.chat.id, lang, False, 
                      transmitted_data=data) 

@bot.message_handler(state=SettingsStates.rename_dino_step_name, is_authorized=True)
async def rename_state(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    async with bot.retrieve_data(userid, message.chat.id) as data:
        dino: Dino = data['dino']
    
    if len(str(message.text)) > 20:
        text = t('rename_dino.err_name', lang, )
        await bot.send_message(message.chat.id, text)
    else:
        await bot.delete_state(userid, message.chat.id)
        await bot.reset_data(message.from_user.id,  message.chat.id)

        last_name = dino.name
        dino.update({'$set': {'name': message.text}})

        text = t('rename_dino.rename', lang, last_name=last_name, dino_name=message.text)
        await bot.send_message(message.chat.id, text, 
                        reply_markup=m(userid, 'last_menu', lang))


