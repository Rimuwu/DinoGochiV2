from telebot.asyncio_filters import AdvancedCustomFilter
from bot.exec import bot
from bot.config import conf, mongo_client

users = mongo_client.bot.users


class IsAdminUser(AdvancedCustomFilter):
    key = 'is_admin'

    async def check(self, message, status):
        is_authorized = message.from_user.id in conf.bot_devs
        
        if status:
            return is_authorized
        else:
            return not is_authorized

class IsAuthorizedUser(AdvancedCustomFilter):
    key = 'is_authorized'

    async def check(self, message, status):
        is_authorized = users.find_one(
                { "userid": message.from_user.id
                }) is not None

        if status:
            return is_authorized
        else:
            return not is_authorized


bot.add_custom_filter(IsAdminUser())
bot.add_custom_filter(IsAuthorizedUser())