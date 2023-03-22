"""Пояснение:
    >>> Стандартный предмет - предмет никак не изменённый пользователем, сгенерированный из базы.
    >>> abilities - словарь с индивидуальными харрактеристиками предмета, прочность, использования и тд.
    >>> preabil - используется только для предмета создаваемого из базы, используется для создания нестандартного предмета.
"""
from bot.config import mongo_client
from bot.const import ITEMS
from bot.modules.data_format import random_dict
from bot.modules.localization import get_all_locales
from bot.modules.localization import get_data as get_loc_data
from bot.modules.logs import log

items_names = {}
items = mongo_client.bot.items

def get_data(itemid: str) -> dict:
    """Получение данных из json"""

    # Проверяем еть ли предмет с таким ключём в items.json
    if itemid in ITEMS['items'].keys():
        return ITEMS['items'][itemid]
    else:
        return {}

def load_items_names() -> dict:
    """Загружает все имена предметов и имена из локалищации в один словарь. 
       Приоритетным является локализация
    """
    items_names = {}

    loc_items_names = get_all_locales('items_names')
    for item_key, item in ITEMS['items'].items():
        items_names[item_key] = item['name']

        for loc_key in loc_items_names.keys():
           loc_name = loc_items_names[loc_key].get(item_key)
           if loc_name:
               items_names[item_key][loc_key] = loc_name['name']
    return items_names

def get_name(itemid: str, lang: str='en') -> str:
    """Получение имени предмета"""
    name = ''
   
    if itemid in items_names:
        if lang not in items_names[itemid]:
            lang = 'en'
        name = items_names[itemid][lang]
    return name

def get_item_dict(itemid: str, preabil: dict = {}) -> dict:
    ''' Создание словаря, хранящийся в инвентаре пользователя.\n

        Примеры: 
            Просто предмет
                >>> f(12)
                >>> {'item_id': "12"}

            Предмет с предустоновленными данными
                >>> f(30, {'uses': 10})
                >>> {'item_id': "30", 'abilities': {'uses': 10}}

    '''
    d_it = {'item_id': itemid, 'abilities': {}}
    data = get_data(itemid)

    if 'abilities' in data.keys():
        abl = {}
        for k in data['abilities'].keys():

            if type(data['abilities'][k]) == int:
                abl[k] = data['abilities'][k]

            elif type(data['abilities'][k]) == dict:
                abl[k] = random_dict(data['abilities'][k])

        d_it['abilities'] = abl

    if preabil != {}:
        if 'abilities' in d_it.keys():
            for ak in d_it['abilities']:
                if ak in preabil.keys():

                    if type(preabil[ak]) == int:
                        d_it['abilities'][ak] = preabil[ak]

                    elif type(preabil[ak]) == dict:
                        d_it['abilities'][ak] = random_dict(preabil[ak])

    return d_it

def is_standart(item: dict) -> bool:
    """Определяем ли стандартный ли предмет*.

    Для этого проверяем есть ли у него свои харрактеристик.\n
    Если их нет - значит он точно стандартный.\n
    Если они есть и не изменены - стандартный.
    Если есть и изменены - изменённый.
    """
    data = get_data(item['item_id'])

    if list(item.keys()) == ['item_id']:
        return True
    else:
        if 'abilities' in item.keys():
            if item['abilities'] == data['abilities']:
                return True
            else:
                return False
        else:
            return True

def AddItemToUser(userid: int, itemid: str, count: int = 1, preabil: dict = {}):
    """Добавление предмета в инвентарь
    """
    assert count <= 0, f'AddItemToUser, count == {count}'

    item = get_item_dict(itemid, preabil)
    find_res = items.find_one({'owner_id': userid, 'items_data': item}, {'_id': 1})

    if find_res:
        items.update_one({'_id': find_res['_id']}, {'$inc': {'count': count}})
        return 'plus count'
    else:
        item_dict = {
            'owner_id': userid,
            'items_data': item,
            'count': count
        }
        items.insert_one(item_dict)
        return 'new item'

def RemoveItemFromUser(userid: int, itemid: str, 
            count: int = 1, preabil: dict = {}):
    """Удаление предмета из инвентаря
       return
       True - всё нормально, удалил
       False - предмета нет или количесвто слишком большое
    """
    assert count <= 0, f'RemoveItemFromUser, count == {count}'

    item = get_item_dict(itemid, preabil)
    find_res = items.find_one({'owner_id': userid, 'items_data': item}, {'_id': 1, 'count': 1})

    if find_res:
        if find_res['count'] - count > 0:
            items.update_one({'_id': find_res['_id']}, 
                            {'$inc': {'count': count * -1}})
            return True
        
        if find_res['count'] - count == 0:
            items.delete_one({'_id': find_res['_id']})
            return True

        if find_res['count'] - count < 0:
            return False
    else:
        return False
    
def item_code(item: dict, v_id: bool = True) -> str:
    """Создаёт код-строку предмета, основываясь на его
       харрактеристиках.
       
       v_id - определяет добавлять ли буквенный индефикатор
    """
    text = ''

    if v_id: text = f"id{item['item_id']}"

    if 'abilities' in item.keys():
        for key, item in item['abilities'].items():
            if v_id:
                text += f".{key[:2]}{item}"
            else:
                text += str(item)
    return text

def decode_item(code: str) -> dict:
    """Превращает код в словарь
    """
    split = code.split('.')
    ids = {
        'us': 'uses', 'en': 'endurance',
        'ma': 'mana', 'st': 'stack'
    }
    data = {}

    for part in split:
        scode = part[:2]
        value = part[2:]
        
        if scode == 'id':
            data['item_id'] = value
        else:
            if 'abilities' not in data.keys(): data['abilities'] = {}
            data['abilities'][ ids[scode] ] = value

    return data

def sort_materials(not_sort_list: list, lang: str, 
                   separator: str = ',') -> str:
    """Создание сообщение нужных материалов для крафта

    Args:
        not_sort_list (list): Список с материалами из базы предметов
          example: [{"item": "26", "type": "delete"}, 
                    {"item": "26", "type": "delete"}]
        lang (str): язык
        separator (str, optional): Разделитель материалов. Defaults to ','.

    Returns:
        str: Возвращает строку для вывода материалов крафта
    """
    col_dict, items_list, check_items = {}, [], []

    # Счмтает предметы
    for i in not_sort_list:
        item = i['item']
        if item not in col_dict: col_dict[item] = 1
        else: col_dict[item] += 1

    # Собирает текст
    for i in not_sort_list:
        item = i['item']
        col = col_dict[item]
        
        if i not in check_items:
            text = get_name(item, lang)
            if i['type'] == 'endurance':
                text += f" (⬇ -{i['act']})"
            if col > 1:
                text += f' x{col_dict[item]}'

            items_list.append(text)
            check_items.append(i)

    return f"{separator} ".join(items_list)

def item_info(item: dict, lang: str):
    standart = ['freezing', 'defrosting', 'dummy', 'material']
    image = None
    
    item_id: str = item['item_id']
    data_item: dict = get_data(item_id)
    item_name: str = get_name(item_id, lang)
    rank_item: str = data_item['rank']
    type_item: str = data_item['type']
    
    loc_d = get_loc_data('item_info', lang)
    text = ''
    
    if type_item in standart:
        text += loc_d['static']['cap'] + '\n'
        text += loc_d['static']['name'].format(name=item_name) + '\n'
        
        rank = loc_d['rank'][rank_item]
        text += loc_d['static']['rank'].format(rank=rank) + '\n'
        
        type_name = loc_d['type_info'][type_item]['type_name']
        text += loc_d['static']['type'].format(type=type_name) + '\n'
        text += loc_d['type_info'][type_item]['add_text']
    
    if 'image' in data_item.keys():
        try:
            image = open(f"images/items/{data_item['image']}.png", 'rb')
        except:
            log(f'Item {item_id} image incorrect', 4)
    
    return text, image

items_names = load_items_names()