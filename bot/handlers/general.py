from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.localization import t
from bot.modules.markup import back_menu, markups_menu as m

users = mongo_client.bot.users

@bot.message_handler(text='buttons_name.back', is_authorized=True)
async def back_buttom(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    back_m = back_menu(userid)
    text = t(f'back_text.{back_m}', lang)

    await bot.send_message(message.chat.id, text, 
                           reply_markup=m(userid, back_m, lang) )

@bot.message_handler(text='commands_name.settings_menu', is_authorized=True)
async def settings_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    user = users.find_one({'userid': userid})
    if user:
        settings = user['settings']
        text = t("menu_text.settings", lang, 
                notif=settings["notifications"], vis_faq=settings['faq'])
        text = text.replace("True", '✅').replace("False", '❌')

        await bot.send_message(message.chat.id, text, 
                               reply_markup=m(userid, 'settings_menu', lang))

@bot.message_handler(text='commands_name.profile_menu', is_authorized=True)
async def profile_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.profile', lang), 
                           reply_markup=m(userid, 'profile_menu', lang))
    
@bot.message_handler(text='commands_name.friends_menu', is_authorized=True)
async def friends_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.friends', lang), 
                           reply_markup=m(userid, 'friends_menu', lang))

@bot.message_handler(text='commands_name.profile.market', is_authorized=True)
async def market_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.market', lang), 
                           reply_markup=m(userid, 'market_menu', lang))

@bot.message_handler(text='commands_name.actions_menu', is_authorized=True)
async def actions_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.actions', lang), 
                           reply_markup=m(userid, 'actions_menu', lang))