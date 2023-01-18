# Фильтр колбека по начальному ключу

from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import CallbackQuery
from bot.exec import bot


class StartWith(AdvancedCustomFilter):
    key = 'startwith'

    async def check(self, callback: CallbackQuery , start_text: str):

        return callback.data.startswith(start_text)


bot.add_custom_filter(StartWith())