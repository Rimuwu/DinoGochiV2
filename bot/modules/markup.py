from telebot.types import ReplyKeyboardMarkup

from bot.config import mongo_client
from bot.modules.data_format import list_to_keyboard
from bot.modules.localization import tranlate_data

users = mongo_client.bot.users

def markups_menu(userid: int, markup_key: str = 'main_menu', language_code: str = 'en') -> ReplyKeyboardMarkup:
    """Главная функция создания меню для клавиатур
       menus:
       main_menu, last_menu
    """
    prefix, buttons = 'commands_name.', []

    if markup_key == 'last_menu':
       """Возращает к последнему меню
       """
       markup_key = users.find_one({'userid': userid}, {'last_markup': 1}) #type: ignore
    
    else: #Сохранение последнего markup
        users.update_one({"userid": userid}, {'$set': {'last_markup': markup_key}})

    if markup_key == 'main_menu':
        """ Главное меню

            Дополнительые аргументы:
            faq - если True, то кнопка справочника не показывается
        """
        buttons = [
            ['dino_profile', 'actions_menu', 'profile_menu'],
            ['settings_menu', 'friends_menu', 'faq'],
            ['dino-tavern_menu']
        ]
        settings = users.find_one({'userid': userid}, {'settings': 1})

        if settings.get('faq', 0): #Если передаём faq, то можно удалить кнопку #type: ignore
            buttons[1].remove('faq')
    
    buttons = tranlate_data(
        data=buttons, 
        locale=language_code, 
        key_prefix=prefix) #Переводим текст внутри списка
    
    return list_to_keyboard(buttons) 
