from telebot.types import ReplyKeyboardMarkup

from bot.config import mongo_client
from bot.const import GAME_SETTINGS as gs
from bot.modules.data_format import chunks, crop_text, list_to_keyboard
from bot.modules.dinosaur import Dino, Egg
from bot.modules.localization import t, tranlate_data
from bot.modules.logs import log
from bot.modules.referals import get_user_code, get_user_sub
from bot.modules.user import User, last_dino, premium

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs
management = mongo_client.bot.management
referals = mongo_client.connections.referals


def back_menu(userid) -> str:
    """Возвращает предыдущее меню
    """
    markup_key = 'main_menu'
    menus_list = ['main_menu', 'settings_menu', 'settings2_menu',
                  'main_menu', 'actions_menu', 
                  'main_menu', 'profile_menu', 'market_menu',
                  'main_menu', 'profile_menu', 'about_menu',
                  'main_menu', 'friends_menu', 'referal_menu',
                  'main_menu', 'dino_tavern_menu', 'dungeon_menu'
                 ] # схема всех путей меню клавиатур
    user_dict = users.find_one(
        {'userid': userid}, {'last_markup': 1}
    )
    if user_dict:
        markup_key = user_dict.get('last_markup', 'main_menu')

    if markup_key != 'main_menu':
        menu_ind = menus_list.index(markup_key)
        result = menus_list[menu_ind - 1]
        return result
    else: return 'main_menu'

def markups_menu(userid: int, markup_key: str = 'main_menu', 
                 language_code: str = 'en', last_markup: bool = False):
    """Главная функция создания меню для клавиатур
       >>> menus:
       main_menu, settings_menu, settings2_menu, profile_menu, about_menu, friends_menu, market_menu, dino_tavern_menu, referal_menu, actions_menu
       last_menu\n\n

       last_markup - Если True, то меню будет изменено только если,
       последнее меню совпадает с тем, на которое будет изменено
       Пример:

       markup_key: settings_menu, last_markup: profile_menu
       >>> last_menu: True -> Меню не изменится
       >>> last_menu: False -> Меню изменится
    """
    prefix, buttons = 'commands_name.', []
    add_back_button = False
    kwargs = {}
    old_last_menu = None
    
    user_dict = users.find_one(
           {'userid': userid}, {'last_markup': 1}
        )

    if markup_key == 'last_menu':
       """Возращает к последнему меню
       """
       user_dict = users.find_one(
           {'userid': userid}, {'last_markup': 1}
        )
       if user_dict:
           markup_key = user_dict.get('last_markup')

    else: #Сохранение последнего markup
        if last_markup:
            user_dict = users.find_one(
                {'userid': userid}, {'last_markup': 1}
                )
            if user_dict:
                old_last_menu = user_dict.get('last_markup')
            
        users.update_one({"userid": userid}, {'$set': {'last_markup': markup_key}})

    if markup_key == 'main_menu':
        # Главное меню
        buttons = [
            ['dino_profile', 'actions_menu', 'profile_menu'],
            ['settings_menu', 'friends_menu'],
            ['dino-tavern_menu']
        ]
    
    elif markup_key == 'settings_menu':
        # Меню настроек
        prefix = 'commands_name.settings.'
        buttons = [
            ['notification', 'inventory'],
            ['dino_name'],
            ['dino_profile', 'delete_me'],
            ['settings_page_2', "noprefix.buttons_name.back"]
        ]

    elif markup_key == 'settings2_menu':
        prefix = 'commands_name.settings2.'
        add_back_button = True
        buttons = [
            ['my_name'],
        ]
        
        if premium(userid): buttons[0].append('custom_profile')

    elif markup_key == 'profile_menu':
        # Меню профиля
        prefix = 'commands_name.profile.'
        add_back_button = True
        buttons = [
            ['information', 'inventory'],
            ['rayting', 'about', 'market'],
        ]

    elif markup_key == 'about_menu':
        # Меню о боте
        prefix = 'commands_name.about.'
        add_back_button = True
        buttons = [
            ['team', 'support'],
            ['faq', 'links'],
        ]

    elif markup_key == 'friends_menu':
        # Меню друзей
        prefix = 'commands_name.friends.'
        add_back_button = True
        buttons = [
            ['add_friend', 'friends_list', 'remove_friend'],
            ['requests', 'referal'],
        ]

    elif markup_key == 'market_menu':
        # Меню рынка
        prefix = 'commands_name.market.'
        add_back_button = True
        buttons = [
            ['random', 'find'],
            ['add_product', 'product_list', 'remove_product'],
        ]

    elif markup_key == 'dino_tavern_menu':
        # Меню таверны
        prefix = 'commands_name.dino_tavern.'
        add_back_button = True
        buttons = [
            ['dungeon', 'quests'],
            ['edit'],
        ]
    
    elif markup_key == 'referal_menu':
        # Меню рефералов
        prefix = 'commands_name.referal.'
        add_back_button = True
        
        referal = get_user_code(userid)
        friend_code = get_user_sub(userid)
        buttons = [
                ['code', 'enter_code'],
            ]
        if referal:
            my_code = referal['code']
            
            buttons[0][0] = f'notranslate.{t("commands_name.referal.my_code", language_code)} {my_code}'
            
        if friend_code:
            buttons[0][1] = f'notranslate.{t("commands_name.referal.friend_code", language_code)} {friend_code["code"]}'

    elif markup_key == 'actions_menu':

        def get_buttons(dino: Dino) -> list:
            data = ['journey', 'put_to_bed', 'collecting', 'entertainments']
            if dino:
                if dino.status == 'journey':
                    data[0] = 'return'
                elif dino.status == 'sleep':
                    data[1] = 'awaken'
                elif dino.status == 'collecting':
                    data[2] = 'progress'
                elif dino.status == 'game':
                    data[3] = 'stop_game'
            return data

        # Меню действий
        prefix = 'commands_name.actions.'
        add_back_button = True
        user = User(userid)
        col_dinos = user.get_col_dinos #Сохраняем кол. динозавров

        if col_dinos == 0:
            buttons = [
                ['no_dino', 'noprefix.buttons_name.back']
            ]
        if col_dinos == 1:
            dino = user.get_dinos()[0]
            dp_buttons = get_buttons(dino)

            buttons = [
                ["feed"],
                [dp_buttons[3], dp_buttons[0]],
                [dp_buttons[1], dp_buttons[2]]
            ]

        else:
            add_back_button = False
            dino = last_dino(user)
            if dino:
                dino_button = f'notranslate.{t("commands_name.actions.dino_button", language_code)} {crop_text(dino.name, 6)}'

                dp_buttons = get_buttons(dino)
                buttons = [
                    ["feed"],
                    [dp_buttons[3], dp_buttons[0]],
                    [dp_buttons[1], dp_buttons[2]],
                    [dino_button, "noprefix.buttons_name.back"]
                ]
    
    else:
        log(prefix='Markup', 
            message=f'not_found_key User: {userid}, Data: {markup_key}', lvl=2)

    buttons = tranlate_data(
        data=buttons, 
        locale=language_code, 
        key_prefix=prefix,
        **kwargs
        ) #Переводим текст внутри списка

    if add_back_button:
        buttons.append([t('buttons_name.back', language_code)])
    
    result = list_to_keyboard(buttons)
    if last_markup:
        user_dict = users.find_one(
           {'userid': userid}, {'last_markup': 1}
        )
        if user_dict:
            if not old_last_menu:
                old_last_menu = user_dict.get('last_markup')

            if old_last_menu != markup_key:
                result = None
    return result

def get_answer_keyboard(elements: list, lang: str='en') -> dict:
    """
       elements - Dino | Egg
    
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
            
        buttons_list = chunks(names, 2) #делим на строчки по 2 элемента
        buttons_list.append([t('buttons_name.cancel', lang)]) #добавляем кнопку отмены
        keyboard = list_to_keyboard(buttons_list, 2) #превращаем список в клавиатуру

        return {'case': 2, 'keyboard': keyboard, 'data_names': data_names}
    
    
def count_markup(max_count: int=1, lang: str='en') -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру для быстрого выбора числа
        Предлагает выбрать 1, max_count // 2, max_count

    Args:
        max_count (int): Максимальное доступное вводимое число
        lang (str): Язык кнопки отмены
    """
    counts = ["x1"]
    if max_count > 1: counts.append(f"x{max_count}")
    if max_count >= 4: counts.insert(1, f"x{max_count // 2}")
    
    return list_to_keyboard([counts, t('buttons_name.cancel', lang)])

def feed_count_markup(dino_eat: int, item_act: int, 
                      max_col: int, item_name: str, lang):
    col_to_full = (100 - dino_eat) // item_act
    one_col = dino_eat + item_act
    return_list = []
    bt_3 = None

    if col_to_full > max_col: col_to_full = max_col
    if one_col > 100: one_col = 100

    bt_1 = f"{one_col}% = {item_name[:1]} x1"
    bt_2 = f"{dino_eat + item_act * col_to_full}% = {item_name[:1]} x{col_to_full}"

    if dino_eat + item_act * col_to_full < 100:
        bt_3 = f"100% = {item_name[:1]} x{col_to_full + 1}"

    if col_to_full == 1:
        if bt_3: return_list += [bt_1, bt_3]
        else: return_list += [bt_1]

    elif col_to_full != 1 and col_to_full != 0:
        if bt_3: return_list += [bt_1, bt_2, bt_3]
        else: return_list += [bt_1, bt_2]
    
    if not return_list: return_list += [bt_1]

    return list_to_keyboard([return_list, [t('buttons_name.cancel', lang)]])

def confirm_markup(lang: str='en') -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру для подтверждения

    Args:
        lang (str, optional):  Язык кнопок
    """
    return list_to_keyboard([
        [t('buttons_name.confirm', lang)], 
        [t('buttons_name.cancel', lang)]]
    )
    
def cancel_markup(lang: str='en') -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру для отмены

    Args:
        lang (str, optional):  Язык кнопки
    """
    return list_to_keyboard([t('buttons_name.cancel', lang)])

def down_menu(markup: ReplyKeyboardMarkup, 
              arrows: bool = True, lang: str = 'en'): 
    """Добавления нижнего меню для страничных клавиатур
    """
    if arrows:
        markup.add(*[gs['back_button'], t('buttons_name.cancel', lang), gs['forward_button']])
    else: markup.add(t('buttons_name.cancel', lang))
    
    return markup