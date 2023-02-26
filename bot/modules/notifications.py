from bot.exec import bot
from bot.modules.localization import t
from bot.modules.logs import log

def dino_notification(dino_id, not_type: str):
    """ Те уведомления, которые нужно отслеживать и отсылать 1 раз
    """
    print(dino_id, not_type)

async def user_notification(user_id: int, not_type: str, lang: str='en', **kwargs):
    """ Те которые в любом случае отправятся 1 раз
    """
    text = not_type
    standart_notification = [
        'incubation_ready'
    ]

    if not_type in standart_notification:
        text = t(f'notifications.{not_type}', lang, **kwargs)

    log(prefix='Notification', 
        message=f'User: {user_id}, Data: {not_type}', lvl=0)
    try:
        await bot.send_message(user_id, text)
    except Exception as error: 
        log(prefix='Notification Error', 
            message=f'User: {user_id}, Data: {not_type} Error: {error}', 
            lvl=3)