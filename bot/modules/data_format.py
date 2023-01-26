import random
from telebot.types import ReplyKeyboardMarkup, User

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


if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")