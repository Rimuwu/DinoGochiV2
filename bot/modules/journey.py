import json
from random import choice, choices, randint

from bot.config import mongo_client
from bot.modules.data_format import random_dict
from bot.modules.dinosaur import end_journey, mutate_dino_stat
from bot.modules.user import get_frineds
from bot.modules.localization import t, get_data
from bot.modules.item import counts_items
from time import time

journey = mongo_client.tasks.journey
dinosaurs = mongo_client.bot.dinosaurs

with open('bot/json/journey.json', encoding='utf-8') as f: 
    JOURNEY = json.load(f) # type: dict

events = {
    ## Только положительные
    "influences_health": {
        'buffs': { # Эффекты на динозавра
            'heal': {
                'positive': {"min": 5, "max": 15, "type": "random"}
                # Эффекты выставляются для первого уровня случайности
                # Если на первом уровне это 5, то на 5-ом это 25
            }
        }
    }, # Повышение здоровья
    "trade_item": {
        "conditions": [ # Заранее заготовленые условия, сработает только при выполнение всех
            'have_item'
        ],
        "actions": [ # Заранее заготовленные действия
            'trade_item'
            ]
    }, # Если динозавр получил какой то предмет, может произойти обмен предмета на монеты / предмет.
    "trade_coins": {
        "conditions": [ # Заранее заготовленые условия, сработает только при выполнение всех
            'have_coins'
        ],
        "actions": [ # Заранее заготовленные действия
            'trade_coins'
        ]
    }, # Если у динозавра есть монеты, он может их обменять на предметы.

    ## Любая позитивность
    "influences_mood": {
        'mood_keys': { # Добавляемые ключи настроения
            'positive': [],
            'negative': []
        }
    },
    "influences_eat": {
        'buffs': { # Эффекты на динозавра
            'eat': {
                'positive': {"min": 5, "max": 15, "type": "random"},
                # Эффекты выставляются для первого уровня случайности
                # Если на первом уровне это 5, то на 5-ом это 25
                'negative': {"min": -10, "max": -2, "type": "random"}
            }
        }
    },
    "influences_game": {
        'buffs': { # Эффекты на динозавра
            'game': {
                'positive': {"min": 5, "max": 15, "type": "random"},
                # Эффекты выставляются для первого уровня случайности
                # Если на первом уровне это 5, то на 5-ом это 25
                'negative': {"min": -10, "max": -2, "type": "random"}
            }
        }
    },
    "influences_energy": {
         'buffs': { # Эффекты на динозавра
            'energy': {
                'positive': {"min": 5, "max": 15, "type": "random"},
                # Эффекты выставляются для первого уровня случайности
                # Если на первом уровне это 5, то на 5-ом это 25
                'negative': {"min": -10, "max": -2, "type": "random"}
            }
        }
    },
    "item": {
        'items': {
            'positive': {
                'weight': [50, 25, 15, 9, 1], # Вес для каждой редкости
                'col': { '1': 1, '2': 1, '3': 1, '4': 1, '5': 1
                }, # Количестово предметов которые нужно удалить в соответсвии с уровнем случайности
                # Не добавляем предметы, они зависят от локации и определяются сами
            }, 
            'negative': {
                'weight': [50, 25, 15, 9, 1],
                'col': { '1': 1, '2': 1, '3': 1, '4': 1, '5': 1
                } # Количестово предметов которые нужно удалить в соответсвии с уровнем случайности
            }
        }
    }, # Добавление / Удаление предмета
    "coins": {
        'coins': { # Эффекты на динозавра
            'positive': {
                '1': {"min": 1, "max": 10, "type": "random"},
                '2': {"min": 20, "max": 50, "type": "random"},
                '3': {"min": 50, "max": 100, "type": "random"},
                '4': {"min": 100, "max": 120, "type": "random"},
                '5': {"min": 150, "max": 210, "type": "random"}
            },
            # Эффекты выставляются для первого уровня случайности
            # Если на первом уровне это 5, то на 5-ом это 25
            'negative': {
                '1': {"min": -5, "max": -1, "type": "random"},
                '2': {"min": -10, "max": -5, "type": "random"},
                '3': {"min": -20, "max": -10, "type": "random"},
                '4': {"min": -50, "max": -20, "type": "random"},
                '5': {"min": -100, "max": -50, "type": "random"}
            }
        }
    }, # Добавление / Удаление монет
    "battle": {
        'mobs': {
            'col': { '1': 1, '2': 1, '3': 2, '4': 2, '5': 3}
        },
        'buffs': { # Эффекты на динозавра
            'energy': {
                'positive': {"min": -10, "max": -2, "type": "random"},
                'negative': {"min": -10, "max": -2, "type": "random"}
            }
        },
        'mood_keys': { # Добавляемые ключи настроения
            'positive': [],
            'negative': []
        }
    }, # Вызывает бой, исход зависит от результат
    "quest": {
        'actions': [
            {'type': 'random_action', 'data': [['delete_items'], ['delete_coins'], []]}
            # Вызывает активность, которая выбирает случайные активности из данных и тем самым может удалить из данных предметы или монеты
        ],
        'items': {
            'positive': {
                'col': { '1': 1, '2': 1, '3': 1, '4': 1, '5': 2},
                'weight': [50, 25, 15, 10, 3]
            }, 
            'negative': {
                'col': { '1': 1, '2': 1, '3': 1, '4': 1, '5': 1},
                'weight': [50, 25, 15, 10, 3]
            }
        },
        'coins': { # Эффекты на динозавра
            'positive': {
                '1': {"min": 1, "max": 10, "type": "random"},
                '2': {"min": 20, "max": 50, "type": "random"},
                '3': {"min": 50, "max": 100, "type": "random"},
                '4': {"min": 100, "max": 120, "type": "random"},
                '5': {"min": 150, "max": 210, "type": "random"}
            },
            'negative': {
                '1': {"min": -3, "max": -1, "type": "random"},
                '2': {"min": -5, "max": -1, "type": "random"},
                '3': {"min": -10, "max": -5, "type": "random"},
                '4': {"min": -20, "max": -10, "type": "random"},
                '5': {"min": -40, "max": -20, "type": "random"}
            }
        }
    }, # Динозавр выполнил / не выполнил задание, получил награду или штраф в монетах

    ## Отрицательные
    "edit_location": {
        'actions': ['edit_location']
        }, # Изменяет локацию, скорее Отрицательное
    "forced_exit": {
        'actions': ['exit']
        }, # Принудительно покидает путешествие

    ## Нет позитивности
    "without_influence": {}, # Влияет только на историю, но не на параметры

    ## Совместные, только если есть совместный дино. Положительные
    # 'joint_event' - оторбажать у совместного дино
    # 'location_friend' - отображать у случайного друга в локации
    "joint_event": {
        "conditions": ['have_friend'],
        'actions': ['random_event', 'joint_event'] # Любое событие
    }, # Запускает другое событие, отображается у обоих динозавров которые ходят вместе. Запускает ту же позитивность
    "joint_activity": {
        "conditions": ['have_friend'],

        'actions': ['random_event', 'joint_event'], # Выбирает из указаных событий если указаны

        'mood_keys': { # Добавляемые ключи настроения
            'positive': []
        }
    }, # Влияет на харрактеристики обоих динозавров (Игра, Настроение, Здоровье, Энергия)
    "meeting_friend": {
        "actions": [ # Заранее заготовленные ействия
            'location_friend', {'type': 'random_event', 'data': 
            ['influences_game', 'influences_mood', 'influences_energy']}
        ],
        'buffs': { # Эффекты на динозавра
            'game': {
                'positive': {"min": 1, "max": 10, "type": "random"}
            }
        },
        'mood_keys': { # Добавляемые ключи настроения
            'positive': []
        }
    }, # Встрева с другом в той же локации, отображается у обоих

    ## Нельзя получить в обычной среде
    "location_event": {}, # Положительное / Отрицательное событие для всех кто находится в локации, ЗАПУСКАТЬ ТОЛЬКО КОДОМ
}

locations = {
    "forest": {
        "danger": 1.0,
        "items": {
            'com': ['jar_honey', 'cookie', 'blank_piece_paper', 'slice_pizza'],
            'unc': ['timer', 'therapeutic_mixture', 'sweet_pancakes', 'fish_oil', 'twigs_tree', 'skin'],
            'rar': ['bento_recipe', 'candy_recipe', 'drink_recipe'],
            'mys': ['salad_recipe', 'torch_recipe', 'popcorn_recipe', 'curry_recipe', 'bread_recipe'],
            'leg': ['soup_recipe', 'gourmet_herbs', 'taco_recipe', 'sandwich_recipe', 'hot_chocolate_recipe']
        },
        "positive": {
            'com': ['influences_mood', 'without_influence', 
                  'influences_eat', 'influences_game'],
            'unc': ['influences_health', 'influences_energy',
                   'joint_activity'],
            'rar': ['coins', 'joint_event', 'meeting_friend'],
            'mys': ['trade_item', 'item'],
            'leg': ['quest', 'coins']
        },
        "negative": {
            'com': ['influences_mood', 'without_influence', 
                  'influences_eat'],
            'unc': ['influences_energy', 'coins'],
            'rar': ['joint_event', 'meeting_friend'],
            'mys': ['item', 'coins'],
            'leg': ['quest', 'edit_location']
        }
    },
    "lost-islands": {
        "danger": 1.1,
        'mobs': {
            'mobs_hp': {},
            'mobs_damage': {},
            'mobs': ['dolphin', 'lobster', 'narwhal', 'orca', 'otter_pup', 'pelican', 'swan', 'whale', 'toucan', 'squid', 'seahorse', 'shark', 'octopus', 'wombat', 'turtle', 'snail', 'sloth', 'skunk', 'sheep', 'seagull', 'rooster', 'pigeon', 'peacock', 'parrot', 'ostrich', 'opossum', 'monkey', 'kangaroo', 'jaguar']
        },
        "items": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        "positive": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        "negative": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        }
    },
    "desert": {
        "danger": 1.4,
        "items": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        'mobs': {
            'mobs_hp': {},
            'mobs_damage': {},
            'mobs': ['lion', 'tiger', 'crocodile', 'snake', 'rhino', 'elephant', 'gorilla', 'camel', 'puma', 'hyena', 'hippo', 'panther', 'coyote', 'giraffe', 'jackal', 'leopard', 'lynx', 'meerkat', 'zebra', 'rattlesnake', 'scorpion']
        },
        "positive": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        "negative": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': ['forced_exit']
        }
    },
    "mountains": {
        "danger": 1.8,
        "items": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        'mobs': {
            'mobs_hp': {},
            'mobs_damage': {},
            'mobs': ['walrus', 'seal', 'reindeer', 'polar_bear', 'penguin', 'moose', 'komodo_dragon', 'goat', 'eagle', 'bear_cub', 'wolf', 'bear', 'owl', 'rabbit', 'weasel', 'grizzly', 'cougar']
        },
        "positive": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        "negative": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': ['forced_exit']
        }
    },
    "magic-forest": {
        "danger": 2.0,
        "items": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        'mobs': {
            'mobs_hp': {},
            'mobs_damage': {},
            'mobs': ['spider', 'fox', 'raccoon', 'deer', 'bat', 'dragon', 'falcon', 'fennec_fox', 'hamster', 'hedgehog', 'lemur', 'lobster', 'meerkat', 'mole', 'red_panda', 'porcupine']
        },
        "positive": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': []
        },
        "negative": {
            'com': [],
            'unc': [],
            'rar': [],
            'mys': [],
            'leg': ['forced_exit']
        }
    },
}

chance = {
    "com": 50, "unc": 25, "rar": 15,
    "mys": 9, "leg": 1
}

rarity_lvl = [0, 'com', 'unc', 'rar', 'mys', 'leg']


def create_event(location: str, worldview: str = '', rarity: int = 0,
                 event: str = ''):
    """ Подготавляивает данные, рандомизируя их
    """
    # Случайная позитивность
    if not worldview:
        if randint(1, 3) == 2:
            worldview = 'negative'
        else: worldview = 'positive'

    # Случайный тип шанса
    if not rarity:
        rarity_chr = choices(list(chance.keys()), list(chance.values()))[0]
        rarity = rarity_lvl.index(rarity_chr)

    # Случайное событие
    loc_data = locations[location]
    if not event: event = choice(loc_data[worldview][rarity_chr]) # type: ignore

    # формирование данны квеста для дальнейшей обработки
    event_data = events[event]
    danger = loc_data['danger']
    data = {'type': event, 'worldview': worldview, 'dino_edit': {}, 
            'location': location}

    if 'buffs' in event_data:
        for key in event_data['buffs']:
            data['dino_edit'][key] = random_dict(
                event_data['buffs'][key][worldview])
            data['dino_edit'][key] = data['dino_edit'][key] + int(
                (data['dino_edit'][key] / 2) * (danger - 1.0))

    for key in ['conditions', 'actions']:
        if key in event_data: data[key] = event_data[key]

    if 'mood_keys' in event_data:
        data['mood_keys'] = event_data['mood_keys'][worldview]

    if 'items' in event_data:
        items_col = event_data['items'][worldview]['col'][str(rarity)]
        data['items'] = []
        for _ in range(items_col):
            if 'weight' in event_data['items'][worldview]:
                item_rar = choices(list(chance.keys()), list(event_data['items'][worldview]['weight']))[0]
            else:
                item_rar = choices(list(chance.keys()), list(chance.values()))[0]
            data['items'].append(choice(loc_data['items'][item_rar]))

    if 'mobs' in event_data:
        ...

    if 'coins' in event_data:
        data['coins'] = random_dict(event_data['coins'][worldview][str(rarity)])
        data['coins'] = data['coins'] + int(
            (data['coins'] / 2) * (danger - 1.0))

    return data

async def random_event(dinoid, location: str, ignored_events: list=[], 
                       friend_dino = None):
    """ Создаёт рандомное событие
    """
    event, res = {}, None

    for _ in range(15):
        for _ in range(10):
            event = create_event(location)
            if event['type'] not in ignored_events: break
        if event:
            res = await activate_event(dinoid, event, friend_dino)
            if res: 
                if event['type'] == 'exit': 
                    end_journey(dinoid)
                    journey.update_one({'dino_id': dinoid}, {'journey_end': int(time())})
                break

    if res: return True
    return False

async def activate_event(dinoid, event: dict, friend_dino = None):
    """ При соответствии условий, создаёт событие
    """
    journey_base = journey.find_one({'dino_id': dinoid}) 

    event_data = events[event['type']]
    if journey_base:
        if 'conditions' in event_data:
            conditions = event_data['conditions']

            if 'have_item' in conditions:
                if len(journey_base['items']) == 0: return False

            elif 'have_coins' in conditions:
                if journey_base['coins'] <= 0: return False

            elif 'have_friend' in conditions:
                if 'friend' not in journey_base: return False

        if 'actions' in event_data:
            actions = event_data['actions']

            for act_dct in actions:
                if type(act_dct) == dict:

                    if act_dct['type'] == 'random_action':
                        rand_list = choice(act_dct['data'])
                        for i in rand_list: actions.append(i)

            if 'delete_items' in actions:
                if 'items' in event: del event['items']

            if 'delete_coins' in actions:
                if 'coins' in event: del event['coins']

            if 'edit_location' in actions:
                new_loc = choice(list(locations.keys()))
                journey_base.update_one({'location': new_loc})
                journey_base['old_location'] = new_loc

            if 'joint_event' in actions:
                if 'friend' in journey_base:
                    if not friend_dino:
                        friend_dino = journey_base['friend']

            if 'random_event' in actions:
                await random_event(dinoid, journey_base['location'], ['joint_event', 'joint_activity', 'meeting_friend'], friend_dino)
                return True

            if 'location_friend' in actions:
                friends = get_frineds(journey_base['sended'])['friends']
                in_loc = []
                for friend_id in friends:
                    res = journey.find({'sended': friend_id, 'location': journey_base['location']})
                    for i in list(res): in_loc.append(i['dino_id'])

                if not in_loc: return False
                else: 
                    if not friend_dino:
                        friend_dino = choice(in_loc)

        if not event['dino_edit']: del event['dino_edit']
        data = {'type': event['type'], 'location': event['location'], 'worldview': event['worldview']}

        if 'coins' in event:
            journey_base['coins'] += event['coins']
            data['coins'] = event['coins']
            if journey_base['coins'] < 0: journey_base['coins'] = 0

            journey.update_one({'_id': journey_base['_id']}, 
                                   {'$set': {'coins': journey_base['coins']}})

        if 'dino_edit' in event:
            data['dino_edit'] = event['dino_edit']
            for key, value in event['dino_edit'].items():

                dino = dinosaurs.find_one({'_id': dinoid})
                if dino: await mutate_dino_stat(dino, key, value)

        if 'items' in event:
            data['items'] = event['items'] 
            for i in data['items']:
                journey.update_one({'_id': journey_base['_id']}, 
                                   {'$push': {'items': i}})

        journey.update_one({'_id': journey_base['_id']}, 
                           {'$push': {'journey_log': data}})
        if friend_dino:
            await activate_event(friend_dino, event, journey_base['dino_id'])
        return True
    return False

def generate_event_message(event: dict, lang: str):
    """ Генерирует сообщение события в путешествие
    """
    location = event['location']
    event_type = event['type']
    worldview = event['worldview']

    signs = get_data('journey.signs', lang)
    text_list = get_data(f'journey.{worldview}.{event_type}', lang)
    text = choice(text_list)
    add = ''

    if 'coins' in event: add += f'{event["coins"]}{signs["coins"]}'
    if 'dino_edit' in event:
        for i in ['heal', 'game', 'energy', 'eat']:
            if i in event['dino_edit']:
                if worldview == 'positive': add = '+'
                add += f'{event["dino_edit"][i]}{signs[i]} '
        add += ' '

    if 'items' in event:
        if worldview == 'positive': add = '+'
        else: add = ' -'

        add += counts_items(event['items'], lang) + ' '

    if 'old_location' in event:
        loc = event['old_location']
        loc_now = get_data(f'journey_start.locations.{location}', lang)['name']
        old_loc = get_data(f'journey_start.locations.{loc}', lang)['name']

        add += f'{old_loc} -> {loc_now}'

    if add: text += f' <code>{add}</code>'
    return text

def all_log(logs: list, lang: str):
    """ Генерирует весь лог событий, возвращает список с сообщениям макс ~1500 символов
    """
    text, n, n_message = '', 0, 0
    messages = ['']

    for event in logs:
        n += 1
        text = f'{n}. {generate_event_message(event, lang)}\n\n'

        if len(messages[n_message]) >= 1500:
            messages.append('')
            n_message += 1
        messages[n_message] += text

    return messages