# Фильтр текста на выбранном языке

from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import Message
from bot.exec import bot
from bot.modules.localization import get_all_locales

commands = {} # {'key.key': [...], }
directirys = ['commands_name', 'buttons_name'] # {'en': {'start_game': ...}, }
for direct in directirys:
    lang_commands = get_all_locales(direct)
    for lang in lang_commands:
        for command_key in lang_commands[lang]:
            commands[f'{direct}.{command_key}'] = commands.get(f'{direct}.{command_key}', [])
            commands[f'{direct}.{command_key}'].append(lang_commands[lang][command_key])

class IsEqual(AdvancedCustomFilter):
    key = 'text'

    async def check(self, message: Message, key: str):
        if commands.get(key, 0):
            return message.text in commands[key]


bot.add_custom_filter(IsEqual())