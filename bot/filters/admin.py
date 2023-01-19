from telebot.asyncio_filters import AdvancedCustomFilter

from bot.config import conf
from bot.exec import bot
from bot.modules.logs import log


class IsAdminUser(AdvancedCustomFilter):
    key = 'is_admin'

    async def check(self, message, status:bool):
        is_authorized = message.from_user.id in conf.bot_devs
        
        if status:
            result = is_authorized
        else:
            result = not is_authorized

        if conf.debug:
            log(prefix='IsAdminUser', message=f'User: {message.from_user.id}, Admin: {is_authorized} -> {result}', lvl=0)

        return result


bot.add_custom_filter(IsAdminUser())