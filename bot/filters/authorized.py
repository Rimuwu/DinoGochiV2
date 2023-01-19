from telebot.asyncio_filters import AdvancedCustomFilter

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.logs import log

users = mongo_client.bot.users


class IsAuthorizedUser(AdvancedCustomFilter):
    key = 'is_authorized'

    async def check(self, message, status:bool):
        is_authorized = users.find_one(
                { 'userid': message.from_user.id
                }) is not None

        if status:
            result = is_authorized
        else:
            result = not is_authorized
        
        if conf.debug:
            log(prefix='IsAuthorizedUser', message=f'User: {message.from_user.id}, Authorized: {is_authorized} -> {result}', lvl=0)

        return result


bot.add_custom_filter(IsAuthorizedUser())