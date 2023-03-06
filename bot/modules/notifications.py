from telebot.types import InlineKeyboardMarkup

from bot.exec import bot
from bot.modules.inline import inline_menu
from bot.modules.localization import get_data, t
from bot.modules.logs import log


def dino_notification(dino_id, not_type: str):
    """ Те уведомления, которые нужно отслеживать и отсылать 1 раз
    """
    print(dino_id, not_type)

async def user_notification(user_id: int, not_type: str, lang: str='en', **kwargs):
    """ Те которые в любом случае отправятся 1 раз
    """
    text, markup_inline = not_type, InlineKeyboardMarkup()
    standart_notification = [
        "donation"
    ]
    unstandart_notification = [
        'incubation_ready' # необходим dino_id 
    ]
    add_way = '.'+kwargs.get('add_way', '')

    if not_type in standart_notification:
        text = t(f'notifications.{not_type}{add_way}', lang, **kwargs)
    
    elif not_type in unstandart_notification:
        data = get_data(f'notifications.{not_type}', lang)
        text = data['text'].format(**kwargs)
        markup_inline = inline_menu(data['inline_menu'], lang, **kwargs)
    
    else:
        log(prefix='Notification not_type', 
            message=f'User: {user_id}, Data: {not_type}', 
            lvl=2)


    log(prefix='Notification', 
        message=f'User: {user_id}, Data: {not_type} Kwargs: {kwargs}', lvl=0)
    try:
        await bot.send_message(user_id, text, reply_markup=markup_inline)
    except Exception as error: 
        log(prefix='Notification Error', 
            message=f'User: {user_id}, Data: {not_type} Error: {error}', 
            lvl=3)