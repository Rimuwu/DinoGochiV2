from telebot.types import ReplyKeyboardMarkup
from bot.modules.localization import tranlate_data
from bot.modules.data_format import list_to_keyboard

def markups_menu(markup_key: str = 'main_menu', language_code: str = 'en', **kwargs) -> ReplyKeyboardMarkup:
    """Главная функция создания меню для клавиатур
    """
    prefix = 'commands_name.'
    buttons = []

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

        if kwargs.get('faq', False): #Если передаём faq, то можно удалить кнопку
            buttons[1].remove('faq')
    
    buttons = tranlate_data(
        data=buttons, 
        locale=language_code, 
        key_prefix=prefix) #Переводим текст внутри списка
    return list_to_keyboard(buttons) 