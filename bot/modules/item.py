"""Пояснение:
    >>> Стандартный предмет - предмет никак не изменённый пользователем, сгенерированный из базы.
    >>> abilities - словарь с индивидуальными харрактеристиками предмета, прочность, использования и тд.
    >>> preabil - используется только для предмета создаваемого из базы, используется для создания нестандартного предмета.
"""
from bot.config import mongo_client
from bot.const import ITEMS
from bot.modules.data_format import random_dict
from bot.modules.localization import get_all_locales

items_names = {}
items = mongo_client.bot.items

def get_data(itemid: str) -> dict:
    """Получение данных из json"""

    # Проверяем еть ли предмет с таким ключём в items.json
    if itemid in ITEMS['items'].keys():
        return ITEMS['items'][itemid]
    else:
        raise Exception(f"The subject with ID {itemid} does not exist.")

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
               items_names[item_key][loc_key] = loc_name

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

def AddItemToUser(userid: int, itemid: str, count: int, preabil: dict = {}):
    """Добавление предмета в инвентарь
    """
    assert count <= 0, f'AddItemToUser, count == {count}'

    item = get_item_dict(itemid, preabil)
    find_res = items.find_one({'owner_id': userid, 'items_data': item}, {'_id': 1})

    if find_res:
        items.update_one({'_id': find_res['_id']}, {'$inc': {'count': count}})
    else:
        item_dict = {
            'owner_id': userid,
            'items_data': item,
            'count': count
        }
        items.insert_one(item_dict)

def RemoveItemFromUser(userid: int, itemid: str, 
            count: int, preabil: dict = {}):
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



items_names = load_items_names()