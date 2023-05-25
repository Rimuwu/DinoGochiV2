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

class StartWith(AdvancedCustomFilter):
    key = 'textstart'

    async def check(self, message: Message, key: str):
        text = t(key, message.from_user.language_code, False)
        return message.text.startswith(text) #type: ignore

bot.add_custom_filter(IsEqual())
bot.add_custom_filter(StartWith())