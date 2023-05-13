from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.localization import t
from bot.modules.markup import markups_menu as m
from bot.modules.user import user_info

users = mongo_client.bot.users

@bot.message_handler(text='commands_name.profile.information', 
                     is_authorized=True)
async def infouser(message: Message):
    userid = message.from_user.id
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    text = user_info(message.from_user, lang)
    photos = await bot.get_user_profile_photos(userid, limit=1)
    if photos.photos:
        photo_id = photos.photos[0][0].file_id #type: ignore
        try:
            await bot.send_photo(chatid, photo_id, text, parse_mode='Markdown')
        except:
            await bot.send_photo(chatid, photo_id, text)
    else:
        try:
            await bot.send_message(message.chat.id, text, parse_mode='Markdown')
        except:
            await bot.send_message(message.chat.id, text)