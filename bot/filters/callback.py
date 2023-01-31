# Фильтр колбека по начальному ключу

from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import CallbackQuery

from bot.exec import bot
from bot.modules.logs import log


class StartWith(AdvancedCustomFilter):
    key = 'startwith'

    async def check(self, callback: CallbackQuery, start_text: str):
        # log(prefix='Callback', message=f'User: {callback.from_user.id}, Data: {callback.data}', lvl=0)
        return callback.data.startswith(start_text)


bot.add_custom_filter(StartWith())