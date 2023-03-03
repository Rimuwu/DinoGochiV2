from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.modules.localization import t
from bot.modules.logs import log


def inline_menu(markup_key: str = 'delete_message', lang: str = 'en', **kwargs):
    markup_inline = InlineKeyboardMarkup()
    text, callback = '-', '-'
    standart_keys = [
        'delete_message', 'send_request',
        'requests', 'dino_profile'
    ]

    if markup_key in standart_keys:
        text = t(f'inline_menu.{markup_key}.text', lang, **kwargs)
        callback = t(f'inline_menu.{markup_key}.callback', lang, **kwargs)

    else:
        log(prefix='InlineMarkup', 
            message=f'not_found_key Data: {markup_key}', lvl=2)
    
    markup_inline.add(
        InlineKeyboardButton(text=text, callback_data=callback))
    return markup_inline