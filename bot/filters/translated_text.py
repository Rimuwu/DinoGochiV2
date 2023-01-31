# Фильтр текста на выбранном языке

from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import Message
from bot.exec import bot
from bot.modules.localization import t


class IsEqual(AdvancedCustomFilter):
    key = 'text'

    async def check(self, message: Message, key: str):
        text = t(key, message.from_user.language_code)
        return text == message.text


bot.add_custom_filter(IsEqual())