from telebot.types import Message
from bot.exec import bot
from bot.modules.data_format import seconds_to_str
from bot.modules.localization import get_lang, t

@bot.message_handler(commands=['timer'])
async def timer(message: Message):
    chatid = message.chat.id
    lang = get_lang(message.from_user.id)

    num, mini, max_lvl = '1', False, 'seconds'
    msg_args = message.text.split() # type: ignore
    if len(msg_args) > 1: num: str = msg_args[1]
    if len(msg_args) > 2: max_lvl: str = msg_args[2]
    if len(msg_args) > 3: mini: bool = bool(msg_args[3])

    if num.isdigit():
        try:
            text = seconds_to_str(int(num), lang, mini, max_lvl)
        except: text = 'error'
        await bot.send_message(chatid, text)

@bot.message_handler(commands=['push_info'])
async def push_info(message: Message):
    chatid = message.chat.id
    lang = get_lang(message.from_user.id)

    text = t('push.push_info', lang)
    await bot.send_message(chatid, text, parse_mode='Markdown')