from telebot.types import ReplyKeyboardMarkup

from bot.config import mongo_client
from bot.modules.data_format import list_to_keyboard, chunks
from bot.modules.localization import tranlate_data, t
from bot.modules.dinosaur import Dino, Egg

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
       markup_key = users.find_one(
           {'userid': userid}, {'last_markup': 1}
        ).get('last_markup') #type: ignore

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

def get_answer_keyboard(elements: list[Dino | Egg], lang: str='en') -> dict:
    """
    
       return 
       {'case': 0} - нет динозавров / яиц
       {'case': 1, 'element': Dino | Egg} - 1 динозавр / яйцо 
       {'case': 2, 'keyboard': ReplyMarkup, 'data_names': dict} - несколько динозавров / яиц
    """
    if len(elements) == 0:
        return {'case': 0}

    elif len(elements) == 1: # возвращает 
        return {'case': 1, 'element': elements[0]}

    else: # Несколько динозавров / яиц
        names, data_names = [], {}
        n, txt = 0, ''
        for element in elements:
            n += 1

            if type(element) == Dino:
                txt = f'{n}🦕 {element.name}' #type: ignore
            elif type(element) == Egg:
                txt = f'{n}🥚'
            
            data_names[txt] = element
            names.append(txt)
            
        buttons_list = list(chunks(names, 2)) #делим на строчки по 2 элемента
        buttons_list.append([t('buttons_name.cancel', lang)]) #добавляем кнопку отмены
        keyboard = list_to_keyboard(buttons_list, 2) #превращаем список в клавиатуру

        return {'case': 2, 'keyboard': keyboard, 'data_names': data_names}