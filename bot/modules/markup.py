from telebot.types import ReplyKeyboardMarkup
from bot.modules.localization import tranlate_data
from bot.modules.data_format import list_to_keyboard
from bot.modules.user import User

def markups_menu(userid: int, markup_key: str = 'main_menu', language_code: str = 'en') -> ReplyKeyboardMarkup:
    """Главная функция создания меню для клавиатур
       menus:
       main_menu, last_menu
    """
    prefix, buttons = 'commands_name.', []
    user = User(userid)

    if markup_key == 'last_menu':
       """Возращает к последнему меню
       """
       markup_key = user.last_markup
    
    else: #Сохранение последнего markup
        user.update({'$set': {'last_markup': markup_key}})

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

        if user.settings.get('faq', 0): #Если передаём faq, то можно удалить кнопку
            buttons[1].remove('faq')
    
    buttons = tranlate_data(
        data=buttons, 
        locale=language_code, 
        key_prefix=prefix) #Переводим текст внутри списка
    
    return list_to_keyboard(buttons) 
