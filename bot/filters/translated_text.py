# Фильтр текста на выбранном языке

from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import Message
from bot.exec import bot
from bot.modules.localization import t, get_lang

class IsEqual(AdvancedCustomFilter):
    key = 'text'

    async def check(self, message: Message, key: str):
        lang = get_lang(message.from_user.id, message.from_user.language_code)
        text = t(key, lang)
        return text == message.text

class StartWith(AdvancedCustomFilter):
    key = 'textstart'

    async def check(self, message: Message, key: str):
        lang = get_lang(message.from_user.id, message.from_user.language_code)
        text = t(key, lang, False)
        return message.text.startswith(text) #type: ignore

bot.add_custom_filter(IsEqual())
bot.add_custom_filter(StartWith())