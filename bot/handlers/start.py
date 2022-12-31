from random import choice
from telebot import types

from bot.exec import bot


@bot.message_handler(commands=["start"], is_authorized=True)
async def start_command(message: types.Message):
    stickers = await bot.get_sticker_set('Stickers_by_DinoGochi_bot')
    sticker = choice(list(stickers.stickers)).file_id
    await bot.send_sticker(message.chat.id, sticker)

@bot.message_handler(commands=["start"], is_authorized=False)
async def start_command(message: types.Message):
    await bot.send_sticker(message.chat.id, 'Not authorized in bot')