from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.types import InlineKeyboardMarkup

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import chunk_pages, list_to_keyboard
from bot.modules.inventory_tools import start_inv
from bot.modules.localization import t
from bot.modules.markup import down_menu, get_answer_keyboard
from bot.modules.markup import markups_menu as m
from bot.modules.user import User

items = mongo_client.bot.items

class GeneralStates(StatesGroup):
    ChooseDino = State() # Состояние для выбора динозавра
    ChooseInt = State() # Состояние для ввода числа
    ChooseString = State() # Состояние для ввода текста
    ChooseConfirm = State() # Состояние для подтверждения (да / нет)
    ChooseOption = State() # Состояние для выбора среди вариантов
    ChooseInline = State() # Состояние для выбора кнопки
    ChoosePagesState = State() # Состояние для выбора среди вариантов, а так же поддерживает страницы
    ChooseCustom = State() # Состояние для кастомного обработчика

def add_if_not(data: dict, userid: int, chatid: int, lang: str):
    """Добавляет минимальные данные для работы"""
    if 'userid' not in data: data['userid'] = userid
    if 'chatid' not in data: data['chatid'] = chatid
    if 'lang' not in data: data['lang'] = lang
    return data

async def ChooseDinoState(function, userid: int, chatid: int, 
        lang: str, add_egg: bool=True, 
        transmitted_data=None):
    """ Устанавливает состояние ожидания динозавра

       В function передаёт 
       >>> element: Dino | Egg, transmitted_data: dict
       
       Return:
        Возвращает 2 если был создано состояние, 1 если завершилось автоматически (1 вариант выбора), 0 - невозможно завершить
    """
    user = User(userid)
    elements = user.get_dinos
    if add_egg: elements += user.get_eggs
    if not transmitted_data: transmitted_data = {}
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    ret_data = get_answer_keyboard(elements, lang)

    if ret_data['case'] == 0:
        await bot.send_message(userid, 
            t('p_profile.no_dinos_eggs', lang),
            reply_markup=m(userid, 'last_menu', lang))
        return False, 'cancel'

    elif ret_data['case'] == 1: #1 динозавр / яйцо, передаём инфу в функцию
        element = ret_data['element']
        await function(element, transmitted_data)
        return False, 'dino'

    elif ret_data['case'] == 2:# Несколько динозавров / яиц
        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, GeneralStates.ChooseDino, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['dino_names'] = ret_data['data_names']
            data['transmitted_data'] = transmitted_data

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=ret_data['keyboard'])
        return True, 'dino'

async def ChooseIntState(function, userid: int, 
                chatid: int, lang: str,
                min_int: int = 1, max_int: int = 10,
                transmitted_data=None):
    """ Устанавливает состояние ожидания числа

        В function передаёт 
        >>> number: int, transmitted_data: dict
        
        Если max_int == 0, значит нет ограничения.
        
        Return:
         Возвращает True если был создано состояние, False если завершилось автоматически (минимальный и максимальный вариант совпадают)
    """
    
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    
    if min_int != max_int:
        await bot.set_state(userid, GeneralStates.ChooseInt, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['transmitted_data'] = transmitted_data
            data['min_int'] = min_int
            data['max_int'] = max_int
        return True, 'int'
    else:
        await function(min_int, transmitted_data)
        return False, 'int'

async def ChooseStringState(function, userid: int, 
                         chatid: int, lang: str,
                         min_len: int = 1, max_len: int = 10,
                         transmitted_data=None):
    """ Устанавливает состояние ожидания сообщения

        В function передаёт 
        >>> string: str, transmitted_data: dict
        
        Return:
         Возвращает True если был создано состояние, не может завершится автоматически
    """
    if not transmitted_data: transmitted_data = {}
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseString, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
        data['min_len'] = min_len
        data['max_len'] = max_len
    return True, 'string'

async def ChooseConfirmState(function, userid: int, 
                         chatid: int, lang: str, cancel: bool=False,
                         transmitted_data=None):
    """ Устанавливает состояние ожидания подтверждения действия

        В function передаёт 
        >>> answer: bool, transmitted_data: dict
        
        cancel - если True, то при отказе вызывает возврат в меню
        
        Return:
         Возвращает True если был создано состояние, не может завершится автоматически
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data['cancel'] = cancel
    
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    await bot.set_state(userid, GeneralStates.ChooseConfirm, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
    return True, 'confirm'

async def ChooseOptionState(function, userid: int, 
                         chatid: int, lang: str,
                         options: dict = {},
                         transmitted_data=None):
    """ Устанавливает состояние ожидания выбора опции

        В function передаёт 
        >>> answer: ???, transmitted_data: dict
        
        Return:
         Возвращает True если был создано состояние, False если завершилось автоматически (1 вариант выбора)
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    
    if len(options) > 1:
        await bot.set_state(userid, GeneralStates.ChooseOption, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['transmitted_data'] = transmitted_data
            data['options'] = options
        return True, 'option'
    else:
        element = options[list(options.keys())[0]]
        await function(element, transmitted_data)
        return False, 'option'

async def ChooseInlineState(function, userid: int, 
                         chatid: int, lang: str,
                         transmitted_data=None):
    """ Устанавливает состояние ожидания нажатия кнопки
        Все ключи callback должны начинаться с 'chooseinline'

        В function передаёт 
        >>> answer: list transmitted_data: dict
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)

    await bot.set_state(userid, GeneralStates.ChooseInline, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
    return True, 'inline'

async def ChooseCustomState(function, custom_handler, 
                         userid: int, 
                         chatid: int, lang: str,
                         transmitted_data=None):
    """ Устанавливает состояние ожидания чего либо, все проверки идут через custom_handler
    
        custom_handler -> bool, Any !
        в custom_handler передаётся (Message, transmitted_data)

        В function передаёт 
        >>> answer: ???, transmitted_data: dict
        
        Return:
         result - второе возвращаемое из custom_handler
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)

    await bot.set_state(userid, GeneralStates.ChooseCustom, chatid)
    async with bot.retrieve_data(userid, chatid) as data:
        data['function'] = function
        data['transmitted_data'] = transmitted_data
        data['custom_handler'] = custom_handler
    return True, 'custom'

async def update_page(pages: list, page: int, chat_id: int, lang: str):
    keyboard = list_to_keyboard(pages[page])
    keyboard = down_menu(keyboard, len(pages) > 1, lang)
    
    await bot.send_message(chat_id, t('optionplus.update_page', lang), reply_markup=keyboard)

async def ChoosePagesState(function, userid: int, 
                         chatid: int, lang: str,
                         options: dict = {}, 
                         horizontal: int=2, vertical: int=3,
                         transmitted_data=None, 
                         autoanswer: bool = True, one_element: bool = True,
                         update_page_function = update_page):
    """ Устанавливает состояние ожидания выбора опции
    
        options = {
            'button_name': data
        }
        
        autoanswer - надо ли делать авто ответ, при 1-ом варианте
        horizontal, vertical - размер страницы
        one_element - будет ли завершаться работа после выбора одного элемента

        В function передаёт 
        >>> answer: ???, transmitted_data: dict
            return 
               - если не требуется ничего обновлять, можно ничего не возвращать.
               - если требуется после какого то элемента удалить состояние - {'status': 'reset'}
               - если требуется обновить страницу с переданными данными - {'status': 'update', 'options': {}} (по желанию ключ 'page')
               - если требуется удалить или добавить элемент, при этом обновив страницу 
               {'status': 'edit', 'elements': {'add' | 'delete': data}}
                 - 'add' - в data требуется передать словарь с ключами, данные объединяются
                 - 'delete' - в data требуется передать список с ключами, ключи будут удалены
        
        В update_page_function передаёт 
        >>> pages: list, page: int, chat_id: int, lang: str
        
        Return:
         Возвращает True если был создано состояние, False если завершилось автоматически (1 вариант выбора)
    """
    if not transmitted_data: transmitted_data = {}
    transmitted_data = add_if_not(transmitted_data, userid, chatid, lang)
    
    # Чанкует страницы и добавляем пустые элементы для сохранения структуры
    pages = chunk_pages(options, horizontal, vertical)
    
    if len(options) > 1 or not autoanswer:
        await bot.set_state(userid, GeneralStates.ChoosePagesState, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['function'] = function
            data['update_page'] = update_page_function
            
            data['transmitted_data'] = transmitted_data
            data['options'] = options
            data['pages'] = pages
            
            data['page'] = 0
            data['one_element'] = one_element
            
            data['settings'] = {'horizontal': horizontal, "vertical": vertical}

        await update_page_function(pages, 0, chatid, lang)
        return True, pages
    else:
        if len(options) == 0: element = None
        else: element = options[list(options.keys())[0]]

        await function(element, transmitted_data)
        return False, pages

chooses = {
    'dino': ChooseDinoState,
    'int': ChooseIntState,
    'str': ChooseStringState,
    'bool': ChooseConfirmState,
    'option': ChooseOptionState,
    'inline': ChooseInlineState,
    'custom': ChooseCustomState,
    'pages': ChoosePagesState,
    'inv': start_inv,
}

async def ChooseStepState(function, userid: int, 
                         chatid: int, lang: str,
                         steps: list = [],
                         transmitted_data=None):
    """ Конвейерная Система Состояний
        Устанавливает ожидание нескольких ответов, запуская состояния по очереди.
        
        steps = [
            {"type": str, "name": str, "data": dict, 
                'message': {'text': str, 'reply_markup': markup}}
        ]
        type - тип опроса пользователя (chooses)
          или 'update_data' c функцией для обновления данных (получает и возвращает transmitted_data) + возвращает ответ для сохранения
          В данных можно указать async: True для асинхронной функции
          Параметр name тоже обязателен.

        name - имя ключа в возвращаемом инвентаре (не повторять для корректности)
        data - данные для функции создания опроса
        message - данные для отправляемо сообщения перед опросом
        translate_message (bool, optional) - если наш текст это чистый ключ из данных, то можно переводить на ходу
            translate_args - словарь с аргументами для перевода
        image (str, optional) - если нам надо отправить картинку, то добавляем сюда путь к ней

        ТОЛЬКО ДЛЯ Inline
          delete_markup  (bool, optional) - удаляет клавиатуру после завершения
        
        delete_user_message (boll, optional) - удалить сообщение пользователя на следующем этапе
        delete_message (boll, optional) - удалить сообщения бота на следующем этапе

        transmitted_data
          edit_message (bool, optional) - если нужно не отсылать сообщения, а обновлять, то можно добавить этот ключ.
          delete_steps (bool, optional) - можно добавить для удаления данных отработанных шагов

        В function передаёт 
        >>> answer: dict, transmitted_data: dict
    """
    if not transmitted_data: transmitted_data = {}
    for step in steps:
        if step['type'] in chooses:
            step['function'] = chooses[step['type']]

            step['data'] = dict(add_if_not(
                step['data'], userid, chatid, lang))
        elif step['type'] == 'update_data': pass
            # В данных уже должен быть ключ function
            # function получает transmitted_data
            # function должна возвращать transmitted_data, answer
        else:
            steps.remove(step)

    transmitted_data = dict(add_if_not(transmitted_data, 
                            userid, chatid, lang))
    
    transmitted_data['steps'] = steps
    transmitted_data['return_function'] = function
    transmitted_data['return_data'] = {}
    await next_step(0, transmitted_data, True)


# Должен быть ниже всех других обработчиков, 
# для возможности их использования
async def next_step(answer, transmitted_data: dict, start: bool=False):
    """Обработчик КСС*

    Args:
        answer (_type_): Ответ переданный из функции ожидания
        transmitted_data (dict): Переданная дата
        start (bool, optional): Является ли функция стартом КСС Defaults to False.
        
        Для фото, добавить в message ключ image с путём до фото

        Для edit_message требуется добавление message_data в transmitted_data.temp
        (Использовать только для inline состояний, не подойдёт для MessageSteps)
    """
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    
    steps = transmitted_data['steps']
    return_data = transmitted_data['return_data']
    temp = {}

    # Обновление внутренних данных
    if not start:
        name = steps[len(return_data)]['name']
        if name:
            transmitted_data['return_data'][name] = answer
        else: print('Имя не указано, бесконечный запрос данных')
        
    if len(return_data) - 1 >= 0:
        last_step = steps[len(return_data) - 1]
        
        if steps[len(return_data) - 1]['type'] == 'inline':
            if 'delete_markup' in last_step and last_step['delete_markup']:
                await bot.edit_message_reply_markup(chatid, last_step['messageid'], reply_markup=InlineKeyboardMarkup())
        
        if 'delete_message' in last_step and last_step['delete_message']:
            await bot.delete_message(chatid, last_step['bmessageid'])

        if 'delete_user_message' in last_step and last_step['delete_user_message']:
            await bot.delete_message(chatid, last_step['umessageid'])

    if len(return_data) != len(steps): #Получение данных по очереди
        ret_data = steps[len(return_data)]

        if ret_data['type'] == 'update_data':
            # Обработчик данных между запросами
            # Не может стоять последней, для этого есть return_function
            if 'async' in ret_data and ret_data['async']:
                transmitted_data, answer = await ret_data['function'](transmitted_data)
            else:
                transmitted_data, answer = ret_data['function'](transmitted_data)

            transmitted_data['return_data'][ret_data['name']] = answer
            ret_data = steps[len(return_data)]

        # Очистка данных
        if 'delete_steps' in transmitted_data and transmitted_data['delete_steps'] and len(return_data) != 0:
            # Для экономия места мы можем удалять данные отработанных шагов
            transmitted_data['steps'][len(return_data)-1] = 0

        if 'temp' in transmitted_data: 
            temp = transmitted_data['temp'].copy()
            del transmitted_data['temp']

        # Следующая функция по счёту
        func_answer, func_type = await ret_data['function'](next_step, 
                    transmitted_data=transmitted_data, **ret_data['data']
        )
        # Отправка если состояние было добавлено и не была завершена автоматически
        if func_type == 'cancel':
            # Если функция возвращает не свой тип, а "cancel" - её надо принудительно завершить
            await bot.delete_state(userid, chatid)
            await bot.reset_data(userid, chatid)
        if func_answer:
            # Отправка сообщения / фото из image, если None - ничего
            if ret_data['message']:
                edit_message = False
                last_message = None
                trans_d = {}

                if 'edit_message' in transmitted_data:
                    edit_message = transmitted_data['edit_message']
                
                if 'message_data' in temp:
                    last_message = temp['message_data']

                if 'translate_message' in ret_data:
                    if ret_data['translate_message']:
                        if 'translate_args' in ret_data:
                            trans_d = ret_data['translate_args']
                        
                        if 'caption' in ret_data['message']:
                            ret_data['message']['caption'] = t(ret_data['message']['caption'], lang, **trans_d)
                        elif 'text' in ret_data['message']:
                            ret_data['message']['text'] = t(ret_data['message']['text'], lang, **trans_d)

                if edit_message and len(return_data) != 0 and last_message:
                    if 'image' in steps[0]:
                        bmessage = await bot.edit_message_caption(
                            chat_id=chatid, message_id=last_message.id,
                            parse_mode='Markdown', **ret_data['message'])
                    else:
                        bmessage = await bot.edit_message_text(
                            chat_id=chatid, message_id=last_message.id, parse_mode='Markdown', **ret_data['message'])
                else:
                    if 'image' in ret_data:
                        photo = open(ret_data['image'], 'rb')

                        bmessage = await bot.send_photo(chatid, photo=photo, parse_mode='Markdown', **ret_data['message'])
                    else:
                        bmessage = await bot.send_message(chatid, parse_mode='Markdown', **ret_data['message'])
                
                ret_data['bmessageid'] = bmessage.id

        # Обновление данных состояния
        if not start and func_answer:
            async with bot.retrieve_data(userid, chatid) as data:
                data['transmitted_data'] = transmitted_data

    else: #Все данные получены
        await bot.delete_state(userid, chatid)
        await bot.reset_data(userid, chatid)

        return_function = transmitted_data['return_function']
        del transmitted_data['return_function']
        del transmitted_data['return_data']

        await return_function(return_data, transmitted_data)
