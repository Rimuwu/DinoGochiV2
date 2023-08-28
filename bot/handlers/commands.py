from telebot.types import Message

from bot.exec import bot
from bot.config import mongo_client
from bot.modules.data_format import seconds_to_str, user_name, str_to_seconds
from bot.modules.inline import inline_menu
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

@bot.message_handler(commands=['string_to_sec'], private=True)
async def string_time(message):
    txt = message.text.replace('/string_to_sec', '')
    chatid = message.chat.id
    lang = get_lang(message.from_user.id)

    if txt == '':
        text = t('string_to_str.info', lang)
        await bot.send_message(chatid, text, parse_mode='Markdown')
    else:
        sec = str_to_seconds(txt)
        await bot.send_message(chatid, str(sec))

@bot.message_handler(commands=['push_info'])
async def push_info(message: Message):
    chatid = message.chat.id
    lang = get_lang(message.from_user.id)

    text = t('push.push_info', lang)
    await bot.send_message(chatid, text, parse_mode='Markdown')

@bot.message_handler(commands=['add_me'], private=False)
async def profile(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)

    name = user_name(message.from_user, False)
    text = t("add_me", lang, userid=userid, username=name)
    await bot.reply_to(message, text, parse_mode='HTML',
                    reply_markup=inline_menu('send_request', lang, userid=userid)
                    )