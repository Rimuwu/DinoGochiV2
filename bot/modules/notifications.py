from telebot.types import InlineKeyboardMarkup

from bot.exec import bot
from bot.modules.inline import inline_menu
from bot.modules.localization import get_data, t
from bot.modules.logs import log
from bson.objectid import ObjectId
from bot.config import mongo_client
from bot.modules.data_format import seconds_to_str

dinosaurs = mongo_client.bot.dinosaurs
dino_owners = mongo_client.connections.dino_owners
users = mongo_client.bot.users

def dino_notification_delete(dino_id: ObjectId, not_type: str):
    ...

async def dino_notification(dino_id: ObjectId, not_type: str, **kwargs):
    """ Те уведомления, которые нужно отслеживать и отсылать 1 раз
        В аргументы автоматически добавляется имя динозавра.

        Если передать add_time_end=True то в аргументы дополнительно будет добавлен ключ
        time_end в формате времени, секудны берутся из ключа secs
    """
    dino = dinosaurs.find_one({"_id": dino_id})
    owners = list(dino_owners.find({'dino_id': dino_id}))
    tracked_notifications = [
        ''
    ]
    text, markup_inline = not_type, InlineKeyboardMarkup()

    async def send_not(text, markup_inline):
        for owner in owners:
            try:
                chat_user = await bot.get_chat_member(owner["owner_id"], owner["owner_id"])
                lang = chat_user.user.language_code
            except:
                lang = 'en'
            if kwargs.get('add_time_end', False):
                kwargs['time_end'] = seconds_to_str(
                    kwargs.get('secs', 0), lang)
                
            data = get_data(f'notifications.{not_type}', lang)
            text = data['text'].format(**kwargs)
            markup_inline = inline_menu(data['inline_menu'], lang, **kwargs)

            log(prefix='DinoNotification', 
                message=f'User: {owner["owner_id"]} DinoId: {dino_id}, Data: {not_type} Kwargs: {kwargs}', lvl=0)
            try:
                await bot.send_message(owner['owner_id'], text, reply_markup=markup_inline)
            except Exception as error: 
                log(prefix='DinoNotification Error', 
                    message=f'User: {owner["owner_id"]} DinoId: {dino_id}, Data: {not_type} Error: {error}', 
                    lvl=3)

    if dino:
        kwargs['dino_name'] = dino['name']
        kwargs['dino_alt_id_markup'] = dino['alt_id']

        if not_type in tracked_notifications:
            if not dino.notifications.get(not_type, False):
                await send_not(text, markup_inline)
                dinosaurs.update_one({'_id': dino_id}, {'$set': 
                                    {f'notifications.{not_type}': True}
                                    })
            else:
                log(prefix='Notification Repeat', 
                    message=f'DinoId: {dino_id}, Data: {not_type} Kwargs: {kwargs}', lvl=0)
        else:
            await send_not(text, markup_inline)

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