from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import Message, CallbackQuery

from bot.config import conf
from bot.exec import bot

class IsPrivateChat(AdvancedCustomFilter):
    key = 'private'

    async def check(self, var, status: bool):
        is_private = var.message.chat.type == 'private'

        if type(var) == CallbackQuery:
            is_private = var.message.chat.type == 'private'
        else: # Message
            is_private = var.chat.type == 'private'

        if status: result = is_private
        else: result = not is_private
        return result

bot.add_custom_filter(IsPrivateChat())