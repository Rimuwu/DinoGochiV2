from telebot.types import Message, User

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_keyboard
from bot.modules.localization import t
from bot.modules.markup import tranlate_data, markups_menu as m
from bot.modules.states import SettingsStates

users = mongo_client.bot.users


async def notification(user: User, result: bool):
    text = t(f'not_set.{result}', user.language_code)
    await bot.send_message(user.id, text, 
                    reply_markup=m(user.id, 
                    'last_menu', user.language_code))
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
                    reply_markup=m(user.id, 
                    'last_menu', user.language_code))
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
                    reply_markup=m(message.from_user.id, 
                    'last_menu', message.from_user.language_code))