#Активация встроенных фильтров
from telebot import asyncio_filters

from bot.exec import bot

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())