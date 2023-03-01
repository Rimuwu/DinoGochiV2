import random
import string

from telebot.types import ReplyKeyboardMarkup, User, InlineKeyboardMarkup, InlineKeyboardButton

from bot.const import GAME_SETTINGS
from bot.modules.localization import get_data


def chunks(lst: list, n: int):
    """Делит список lst, на списки по n элементов
       Возвращает генератор
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
    
def random_dict(data: dict[str, int]) -> int | dict:
    """ Предоставляет общий формат данных, подерживающий 
        случайные и статичные числа.
    
    Примеры словаря:
        >>> {"min": 1, "max": 2, "type": "random"}
        >>> {"act": 1, "type": "static"}
    """

    if 'type' not in data:
        return data

    if data["type"] == "static":
        return data['act']

    elif data["type"] == "random":
        if data['min'] >= data['max']:
            return 0
        else:
            return random.randint(data['min'], data['max'])

    return 0

def list_to_keyboard(buttons: list, row_width: int = 3, resize_keyboard: bool = True, one_time_keyboard = None) -> ReplyKeyboardMarkup:
    '''Превращает список со списками в объект клавиатуры.
        Example:
            butttons = [ ['привет'], ['отвяжись', 'ты кто?'] ]

        >      привет
          отвяжись  ты кто?
        
            butttons = ['привет','отвяжись','ты кто?'], 
            row_width = 1

        >  привет
          отвяжись  
          ты кто?
    '''
    markup = ReplyKeyboardMarkup(row_width=row_width, 
                                 resize_keyboard=resize_keyboard, 
                                 one_time_keyboard=one_time_keyboard)

    if len(buttons) == 1:
        markup.add(*[i for i in buttons])

    else:
        for line in buttons:
            markup.row(*[i for i in line])

    return markup

def list_to_inline(buttons: list[dict], row_width: int = 3) -> InlineKeyboardMarkup:
    '''Превращает список со списками в объект inlineKeyboard.
        Example:
            butttons = [ {'привет':'call_key'}, {'отвяжись':'call_key'}, {'ты кто?':'call_key'} ]

        >      привет
          отвяжись  ты кто?
        
            butttons = [ {'привет':'call_key', 'отвяжись':'call_key', 'ты кто?':'call_key'} ], 
            row_width = 1

        >  привет
          отвяжись  
          ты кто?
    '''
    inline = InlineKeyboardMarkup(row_width=row_width)

    if len(buttons) == 1:
        inline.add(
            *[InlineKeyboardButton(
            text=key, callback_data=item) for key, item in buttons[0].items()]
              )

    else:
        for line in buttons:
            inline.row(*[InlineKeyboardButton(
                text=key, callback_data=item) for key, item in line.items()]
                       )

    return inline

def user_name(user: User) -> str:
    """Возвращает имя / ник, в зависимости от того, что есть
    """
    if user.username is not None:
        return user.username
    else:
        if user.last_name is not None and user.first_name:
            return f'{user.first_name} {user.last_name}'
        else:
            return user.first_name

def random_quality() -> str:
    """Случайная редкость
    """
    rarities = list(GAME_SETTINGS['dino_rarity'].keys())
    weights = list(GAME_SETTINGS['dino_rarity'].values())

    quality = random.choices(rarities, weights)[0]
    return quality

def random_code(length: int=10):
    """Генерирует случайный код из букв и цыфр
    """
    alphabet = string.ascii_letters + string.digits

    code = ''.join(random.choice(alphabet) for i in range(length))

    return code

def seconds_to_str(seconds: int, lang: str='en', mini: bool=False):
    """Преобразует число секунд в строку
       Example:
       > seconds=10000 lang='ru'
       > 1 день 2 минуты 41 секунда
       
       > seconds=10000 lang='ru' mini=True
       > 1д. 2мин. 41сек.
    """
    time_format = dict(get_data('time_format', lang)) # type: dict
    result = ''

    def ending_w(time_type: str, unit: int) -> str:
        """Опредеяет окончание для слова
        """
        if mini:
            return time_format[time_type][3]
        
        else:
            result = ''
            if unit < 11 or unit > 14:
                unit = unit % 10

            if unit == 1:
                result = time_format[time_type][0]
            elif unit > 1 and unit <= 4:
                result = time_format[time_type][1]
            elif unit > 4 or unit == 0:
                result = time_format[time_type][2]
        
        return result
    
    def seconds_to_time(seconds: int) -> dict:
        """Преобразует число в словарь
        """
        time_calculation = {
            'day': 86400, 'hour': 3600, 
            'minute': 60, 'second': 1
        }
        time_dict = {
            'day': 0, 'hour': 0, 
            'minute': 0, 'second': 0
        }

        for tp, unit in time_calculation.items():
            tt = seconds // unit

            if tt:
                seconds -= tt * unit
                time_dict[tp] = tt
        
        return time_dict 

    data = seconds_to_time(seconds=seconds)
    for tp, unit in data.items():
        if unit:
            if mini:
                result += f'{unit}{ending_w(tp, unit)} '
            else:
                result += f'{unit} {ending_w(tp, unit)} '
    
    return result

def near_key_number(n: int, data: dict, alternative: int=1):
    """Находит ближайшее меньшее число среди ключей.
       В словаре ключи должны быть str(числами), в порядке убывания

       Пример:
        n=6 data={'10': 'много', '5': 'средне', '2': 'мало'}
        >>> 5, средне #key, value

        alterantive - если не получилось найти ключ, будет возвращён
    """
    for key in data.keys():
        if int(key) <= n:
            return data[key]
    return data[alternative]

def crop_text(text: str, unit: int=10, postfix: str='...'):
    """Обрезает текст и добавляет postfix в конце, 
       если текст больше чем unit + len(postfix)
    """
    if len(text) > unit + len(postfix):
        return text[:unit] + postfix
    else:
        return text