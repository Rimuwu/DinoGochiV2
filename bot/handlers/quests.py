from telebot.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, InputMedia)

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.localization import get_data, t
from bot.modules.currency import get_all_currency, get_products
from bot.modules.item import counts_items
from bot.modules.data_format import seconds_to_str

@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('quest'))
async def quest(call: CallbackQuery):
    chatid = call.message.chat.id
    userid = call.from_user.id
    data = call.data.split()
    lang = call.from_user.language_code
    
    print(data)