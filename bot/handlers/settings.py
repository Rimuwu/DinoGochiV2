from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.localization import t
from bot.modules.markup import markups_menu as m

users = mongo_client.bot.users

@bot.message_handler(text='commands_name.settings_menu', is_authorized=True)
async def settings_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    user = users.find_one({'userid': userid})
    if user:
        settings = user['settings']
        text = t("open_settings", lang, 
                notif=settings["notifications"], vis_faq=settings['faq'])
        text = text.replace("True", '✅').replace("False", '❌')

        await bot.send_message(message.chat.id, text, reply_markup=m(userid, 'settings_menu', lang))

    