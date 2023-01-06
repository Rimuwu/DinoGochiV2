from telebot.asyncio_filters import AdvancedCustomFilter
from bot.exec import bot
from bot.config import conf


class IsAdminUser(AdvancedCustomFilter):
    key = 'is_admin'

    async def check(self, message, status:bool):
        is_authorized = message.from_user.id in conf.bot_devs
        
        if status:
            return is_authorized
        else:
            return not is_authorized

bot.add_custom_filter(IsAdminUser())