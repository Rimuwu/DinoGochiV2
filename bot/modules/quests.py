from random import choice, randint
from time import time

from bot.const import ITEMS, QUESTS
from bot.modules.data_format import random_dict, list_to_inline, seconds_to_str, random_code
from bot.modules.item import counts_items, get_name
from bot.modules.localization import get_data, t
from bot.config import mongo_client
from bson.objectid import ObjectId

quests_data = mongo_client.bot.quests

complex_time = {
    1: {"min": 36000, "max": 57600, "type": "random"},
    2: {"min": 86400, "max": 172800, "type": "random"},
    3: {"min": 259200, "max": 432000, "type": "random"},
    4: {"min": 604800, "max": 864000, "type": "random"},
    5: {"min": 864000, "max": 1209600, "type": "random"},
}

EAT_DATA = {}

def save_eat_items():
    eat_data = {}

    for key, item in ITEMS.items():
        if item['type'] == 'eat':
            if item['rank'] in eat_data:
                eat_data[item['rank']].append(key)
            else:
                eat_data[item['rank']] = [key]
    return eat_data

def create_quest(complexity: int, qtype: str=''):
    """ Создание данных для квеста
        complexity - [1, 5]
    """
    quests = []
    assert 1 <= complexity <= 5, f"1 <= {complexity} <= 5"

    if not qtype:
        types = ['feed', 'collecting', 'fishing', 'journey', 'game', 'get']
        # 'kill', 
        qtype = choice(types)

    for quest in QUESTS:
        if quest['type'] == qtype and quest['complexity'] == complexity:
            quests.append(quest)

    if quests:
        quest_data, count = choice(quests), 0
        coins_one = random_dict(quest_data['reward']['coins'])

        quest = {
            'reward': {'coins': 0, 'items': []},
            'complexity': complexity,
            'type': qtype,
            'data': {}
        }

        if qtype == 'get':
            quest['data']['items'] = []
            col_items = random_dict(quest_data['data']['count'])
            for _ in range(col_items):
                quest['data']['items'].append(choice(quest_data['data']['items']))

        elif qtype in ['journey', 'game']:
            quest['data']['minutes'] = [random_dict(quest_data['data']['minutes']), 0]

        elif qtype in ['fishing', 'collecting', 'hunt']:
            count = random_dict(quest_data['data']['count'])
            quest['data']['count'] = [count, 0]

        elif qtype == 'feed':
            count = random_dict(quest_data['data']['count'])
            eat_rank = random_dict(quest_data['data']['eat_rare'])
            data_items = {}

            temp_count = count
            while temp_count > 0:
                if temp_count != 1:
                    n = randint(1, temp_count)
                else: n = 1
                temp_count -= n
                random_item = choice(EAT_DATA[eat_rank])

                data_items[random_item] = [n, 0]

            quest['data']['items'] = data_items

        if count:
            coins = coins_one * count
        else: coins = coins_one

        quest['reward']['coins'] = coins

        authors = get_data('quests.authors')
        quest['author'] = authors.index(choice(authors))

        names = get_data(f'quests.{qtype}')
        quest['name'] = names.index(choice(names))

        quest['time_end'] = int(time()) + random_dict(complex_time[complexity])
        quest['time_start'] = int(time())

        return quest
    else: return {}

def quest_ui(quest: dict, lang: str, quest_id: str=''):
    """ Генерация текста и клавиатуры о квесте
    """
    text = ''

    name = get_data(f'quests.{quest["type"]}', lang)[quest["name"]]
    author = get_data(f'quests.authors', lang)[quest["author"]]
    text += t('quest.had', lang, 
              name=name, author=author) + '\n\n'
    complexity = t('quest.comp_element', lang) * quest['complexity']
    text += t('quest.complexity', lang, complexity=complexity) + '\n'

    qtype = t(f'quest.types.{quest["type"]}', lang)
    text += t('quest.type', lang, qtype=qtype) + '\n\n'

    if quest['type'] == 'get':
        items_list = counts_items(quest['data']['items'], lang)
        text += t('quest.get', lang, items_list=items_list)

    elif quest['type'] == 'game':
        minutes, now = quest['data']['minutes']
        text += t('quest.game', lang, min=minutes, now=now)

    elif quest['type'] == 'journey':
        minutes, now = quest['data']['minutes']
        text += t('quest.journey', lang, min=minutes, now=now)

    elif quest['type'] == 'feed':
        eat_list = ''
        for ikey, ivalue in quest['data']['items'].items():
            eat_list += f'{get_name(ikey, lang)}: {ivalue[1]} / {ivalue[0]}\n'
        text += t('quest.feed', lang, eat_list=eat_list)[:-1]

    elif quest['type'] == 'collecting':
        cmax, now = quest['data']['count']
        text += t('quest.collecting', lang, max=cmax, now=now)

    elif quest['type'] == 'fishing':
        cmax, now = quest['data']['count']
        text += t('quest.fishing', lang, max=cmax, now=now)

    elif quest['type'] == 'hunt':
        cmax, now = quest['data']['count']
        text += t('quest.hunt', lang, max=cmax, now=now)

    text += '\n\n' + t('quest.reward.had', lang) + '\n'
    if quest['reward']['coins']:
        text += t('quest.reward.coins', lang, coins=quest['reward']['coins'])
    if quest['reward']['items']:
        text = counts_items(quest['reward']['items'], lang)

    time_end = quest['time_end'] - quest['time_start']
    text += '\n\n' + t('quest.time_end', lang, time_end=seconds_to_str(time_end, lang))

    buttons = {}
    if quest_id:
        tb: dict = get_data('quest.buttons', lang)
        for key, value in tb.items():
            buttons[value] = key + ' ' + quest_id

    markup = list_to_inline([buttons], 2)
    return text, markup

def save_quest(quest: dict, owner_id: int): 
    """ Сохраняет квест в базе
    """
    
    def generation_code():
        code = random_code(10)
        if quests_data.find_one({'alt_id': code}):
            code = generation_code()
        return code

    quest['alt_id'] = generation_code()
    quest['owner_id'] = owner_id

    quests_data.insert_one(quest)

def quest_resampling(questid: ObjectId):
    """ Убирает владельца квеста, тем самым предоставляя квест для распределния на новых участников
    """
    quests_data.update_one({'_id': questid}, {'owner_id': 0})

EAT_DATA = save_eat_items()