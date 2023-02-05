import random
import string

from telebot.types import ReplyKeyboardMarkup, User

from bot.modules.localization import get_data


def chunks(lst: list, n: int):
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


def list_to_keyboard(
    buttons: list, 
    row_width: int = 3, 
    resize_keyboard: bool = True, 
    one_time_keyboard = None) -> ReplyKeyboardMarkup:
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
    markup = ReplyKeyboardMarkup(
            row_width=row_width, 
            resize_keyboard=resize_keyboard, 
            one_time_keyboard=one_time_keyboard)

    if len(buttons) == 1:
        markup.add(*[i for i in buttons])

    else:
        for line in buttons:
            markup.row(*[i for i in line])

    return markup

def user_name(user: User):

    if user.username is not None:
        return user.username
    else:
        if user.last_name is not None and user.first_name:
            return f'{user.first_name} {user.last_name}'
        else:
            return user.first_name

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
       > 1 д. 2 мин. 41 сек.
    """
    time_format = dict(get_data('time_format', lang)) # type: dict
    result = ''

    def ending_w(time_type: str, unit: int) -> str:
        if mini:
            return time_format[time_type][3]
        
        else:
            result = ''
            if int(unit) not in [11, 12, 13, 14, 15]:
                number = int(str(unit)[int(len(str(unit))) - 1:])
            else:
                number = int(unit)
                
            if number == 1:
                result = time_format[time_type][0]
            elif number in [2, 3, 4]:
                result = time_format[time_type][1]
            elif number > 4 or number == 0:
                result = time_format[time_type][2]
        
        return result
    
    def seconds_to_time(seconds: int):
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



if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")