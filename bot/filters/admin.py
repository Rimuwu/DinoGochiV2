import telebot
from bot.exec import bot
from bot.config import conf, mongo_client

users = mongo_client.bot.users


class IsAdminUser(telebot.asyncio_filters.AdvancedCustomFilter):
    key = 'is_admin'

    async def check(self, message, status:bool):
        is_authorized = message.from_user.id in conf.bot_devs
        
        if status:
            return is_authorized
        else:
            return not is_authorized

bot.add_custom_filter(IsAdminUser())