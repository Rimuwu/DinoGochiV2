from telebot.types import Message, CallbackQuery

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_keyboard, chunks
from bot.modules.localization import t, get_data
from bot.modules.markup import tranlate_data, markups_menu as m
from bot.modules.states_tools import ChooseDinoState, ChooseOptionState, ChooseStringState, ChooseConfirmState
from bot.modules.dinosaur import Dino
from bot.modules.user import premium

users = mongo_client.bot.users


async def notification(result: bool, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    text = t(f'not_set.{result}', lang)
    await bot.send_message(chatid, text, 
                    reply_markup=m(userid, 'last_menu', lang))
    users.update_one({'userid': userid}, {"$set": {'settings.notifications': result}})

@bot.message_handler(text='commands_name.settings.notification', 
                     is_authorized=True)
async def notification_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    prefix = 'buttons_name.'
    buttons = [
        ['enable', 'disable'],
        ['cancel']
    ]
    translated = tranlate_data(buttons, lang, prefix)
    keyboard = list_to_keyboard(translated, 2)
    
    await ChooseConfirmState(notification, userid, chatid, lang)
    await bot.send_message(userid, t('not_set.info', lang), 
                           reply_markup=keyboard)


async def faq(result: bool, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    text = t(f'settings_faq.{result}', lang)
    await bot.send_message(chatid, text, 
                    reply_markup=m(userid, 'last_menu', lang))
    users.update_one({'userid': userid}, {"$set": {'settings.faq': result}})

@bot.message_handler(text='commands_name.settings.faq', 
                     is_authorized=True)
async def faq_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    prefix = 'buttons_name.'
    buttons = [
        ['enable', 'disable'],
        ['cancel']
    ]
    translated = tranlate_data(buttons, lang, prefix)
    keyboard = list_to_keyboard(translated, 2)

    await ChooseConfirmState(faq, userid, chatid, lang)
    await bot.send_message(userid, t('settings_faq.info', lang), 
                           reply_markup=keyboard)


async def dino_profile(result: bool, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    data = get_data('profile_view.ans', lang)
    text = t(f'profile_view.result', lang, res = data[result-1])
    await bot.send_message(chatid, text, 
                    reply_markup=m(userid, 
                    'last_menu', lang))
    users.update_one({'userid': userid}, {"$set": {'settings.profile_view': result}})

@bot.message_handler(text='commands_name.settings.dino_profile', 
                     is_authorized=True)
async def dino_profile_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    settings_data, time_list = {}, []

    for i in get_data('profile_view.ans', lang):
        time_list.append(i)
        ind = time_list.index(i) + 1
        settings_data[i] = ind

    buttons = chunks(time_list, 2)
    buttons.append([t('buttons_name.cancel', lang)])

    keyboard = list_to_keyboard(buttons, 2)
    await ChooseOptionState(dino_profile, userid, chatid, lang, settings_data)
    await bot.send_message(userid, t('profile_view.info', lang), 
                           reply_markup=keyboard)


async def inventory(result: list, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    text = t(f'inv_set_pages.accept', lang, 
             gr = result[0], vr = result[1]
             )
    await bot.send_message(chatid, text, 
                    reply_markup=m(userid, 'last_menu', lang))
    users.update_one({'userid': userid}, {"$set": {'settings.inv_view': result}})

@bot.message_handler(text='commands_name.settings.inventory', 
                     is_authorized=True)
async def inventory_set(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    settings_data, time_list = {}, []

    for i in get_data('inv_set_pages.ans', lang):
        time_list.append(i)
        settings_data[i] = list(int(strn) for strn in i.split(' | '))

    buttons = chunks(time_list, 2)
    buttons.append([t('buttons_name.cancel', lang)])
    keyboard = list_to_keyboard(buttons, 2)

    await ChooseOptionState(inventory, userid, chatid, lang, settings_data)
    await bot.send_message(userid, t('inv_set_pages.info', lang), 
                           reply_markup=keyboard)
    

async def rename_dino_post_state(content: str, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    dino = transmitted_data['dino']

    last_name = dino.name
    dino.update({'$set': {'name': content}})

    text = t('rename_dino.rename', lang, 
             last_name=last_name, dino_name=content)
    await bot.send_message(chatid, text, 
                    reply_markup=m(userid, 'last_menu', lang))


async def transition(dino: Dino, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    text = t('rename_dino.info', lang, last_name=dino.name)
    keyboard = [t('buttons_name.cancel', lang)]
    markup = list_to_keyboard(keyboard, one_time_keyboard=True)

    data = {
        'dino': dino
    }
    await ChooseStringState(rename_dino_post_state, userid, 
                            chatid, lang, max_len=20, transmitted_data=data)

    await bot.send_message(userid, text, reply_markup=markup)

@bot.message_handler(text='commands_name.settings.dino_name', 
                     is_authorized=True)
async def rename_dino(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await ChooseDinoState(transition, userid, message.chat.id, lang, False)


async def custom_profile_adapter(content: str, transmitted_data: dict):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    text = t('custom_profile.ok', lang)
    await bot.send_message(chatid, text, 
                           reply_markup=m(userid, 'last_menu', lang))
    
    users.update_one({'userid': userid}, 
                     {'$set': {'settings.custom_url': content}})
    

@bot.message_handler(text='commands_name.settings.custom_profile', 
                     is_authorized=True)
async def custom_profile(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    if premium:
        markup = list_to_keyboard([t('buttons_name.cancel', lang)])
        text = t('custom_profile.manual', lang)
        await bot.send_message(userid, text, reply_markup=markup)
        await ChooseStringState(custom_profile_adapter, userid, chatid, lang, max_len=200)
    else:
        text = t('custom_profile.no_premium', lang)
        await bot.send_message(userid, text)

@bot.callback_query_handler(is_authorized=True, 
                            func=lambda call: call.data.startswith('rename_dino'))
async def rename_button(callback: CallbackQuery):
    dino_data = callback.data.split()[1]
    lang = callback.from_user.language_code
    userid = callback.from_user.id
    chatid = callback.message.chat.id
    
    trans_data = {
        'userid': userid,
        'chatid': chatid,
        'lang': lang
    }
    dino = Dino(dino_data) #type: ignore
    await transition(dino, trans_data)

    