import pymongo
import threading

import time
from pprint import pprint
import random
import string


client = pymongo.MongoClient('localhost', 27017)

old_users, users, dinosaurs, items, friends = client.bot.old_users, client.bot.users, client.bot.dinosaurs, client.bot.items, client.connections.friends

incubation = client.tasks.incubation
dino_owners = client.connections.dino_owners
referals = client.connections.referals

def random_code(length: int=10):
    """Генерирует случайный код из букв и цыфр
    """
    alphabet = string.ascii_letters + string.digits

    code = ''.join(random.choice(alphabet) for i in range(length))

    return code


def qr_item_code(item: dict, v_id: bool = True):
        if v_id == True:
            text = f"i{item['item_id']}"
        else:
            text = ''

        if 'abilities' in item.keys():

            if 'uses' in item['abilities'].keys():
                # u - ключ код для des_qr

                if v_id == True:
                    text += f".u{item['abilities']['uses']}"
                else:
                    text += f"{item['abilities']['uses']}"

            if 'endurance' in item['abilities'].keys():
                # e - ключ код для des_qr

                if v_id == True:
                    text += f".e{item['abilities']['endurance']}"
                else:
                    text += f"{item['abilities']['endurance']}"

            if 'mana' in item['abilities'].keys():
                # m - ключ код для des_qr

                if v_id == True:
                    text += f".m{item['abilities']['mana']}"
                else:
                    text += f"{item['abilities']['mana']}"

            if 'stack' in item['abilities'].keys():
                # s - ключ код для des_qr

                if v_id == True:
                    text += f".s{item['abilities']['stack']}"
                else:
                    text += f"{item['abilities']['stack']}"

        return text


def new_referal(user_id, code, frined_code):

    ref = {
        'user_id': user_id,
        'user_code': code, 
        'frined_code': frined_code
    }

    referals.insert_one(ref)

def new_user(userid, last_markup, 
        last_message_time, notifications, faq,
        profile_view, inv_view,
        coins, lvl, xp, dead_dinos, dung_stats, quests, referal_system
        ):
    
    if last_markup == 1:
        last_markup = 'main_menu'
    
    user = {
        'userid': userid,

        'last_markup': last_markup,
        'last_message_time': last_message_time,

        'settings': {
            'notifications': notifications,
            'faq': faq,
            'last_dino': None,
            'profile_view': profile_view, # 1
            'inv_view': inv_view, # [2, 3]
            'premium_status': 0
        },

        'dungeon': {
            'statistics': dung_stats,
            'quests': quests
        },

        'coins': coins, 'lvl': lvl,
        'xp': xp, 'dead_dinos': dead_dinos
    }

    if referal_system:
        new_referal(userid, referal_system['my_cod'], 
                    referal_system.get('friend_cod', None))

    if users.find_one({'userid': userid}) is None:
        users.insert_one(user)

def new_friends(userid, friendid, tp):
    lst = [userid, friendid]

    res1 = friends.find_one({
        "userid": lst[0], 
        "friendid": lst[1], 
        'type': tp
        })
    res2 = friends.find_one(
        {"userid": lst[1], 
         "friendid": lst[0], 
         'type': tp
        })

    if res1 == None and res2 == None:

        frineds_l = {
            'userid': lst[0],
            'friendid': lst[1],
            'type': tp
        }
        friends.insert_one(frineds_l)

def new_dino(owner_id, dino_id, status, 
             name, quality, heal, eat, 
             game, mood, energy, acs):

    dino = {
        'data_id': dino_id,
        'alt_id': f'{owner_id}_{random_code(8)}',

        'status': status,
        'name': name,
        'quality': quality, 

        'notifications': {},

        'stats': {
            'heal': heal,
            'eat': eat,
            'game': game, 
            'mood': mood,
            'energy': energy,
        },

        'activ_items': acs,

        "memory": {
            'games': [],
            'eat': []
        },
        
    }
    result = dinosaurs.insert_one(dino)

    con = {
        'dino_id': result.inserted_id,
        'owner_id': owner_id, 
        'type': 'owner'
    }
    dino_owners.insert_one(con)

def new_egg(incubation_time, egg_id, owner_id,):
    egg = {
        "incubation_time": int(incubation_time),
        "egg_id": egg_id,
        "owner_id": owner_id,
        "quality": "random",
        "dino_id": 0
    }

    incubation.insert_one(egg)

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

users_list = list(old_users.find({}))
users_list.reverse()
print('start')

def work(users_list):
    col = len(users_list)
    n = 0
    for u in users_list:
        n += 1
        #юзер
        new_user(u['userid'], u['settings'].get('last_markup', 'main_menu'),
                u['last_m'], 
                u['settings']['notifications'], u['settings'].get('vis.faq', True),
                u['settings'].get('profile_view', 1),
                [2, 3], u['coins'], u['lvl'][0],
                u['lvl'][1], u.get('dead_dinos', 0), u.get('user_dungeon', {'statistics': []})['statistics'],
                u.get('user_dungeon', {}).get('quests', {
                                        "activ_quests": [],
                                        "max_quests": 5,
                                        "ended": 0
                                        }),
                
                u.get('referal_system', None)
        )

        for friend in u['friends']['friends_list']:
            new_friends(u['userid'], friend, 'friends')
        
        for friend in u['friends']['requests']:
            new_friends(u['userid'], friend, 'request')

        # предметы
        items_dict = {}
        for item in u['inventory']:
            i_qr = qr_item_code(item)

            if i_qr in items_dict.keys():
                items_dict[i_qr]['count'] += 1
            
            else:
                items_dict[i_qr] = {
                    'owner_id': u['userid'], 
                    'items_data': item, 
                    'count': 1
                    }
        
        for ikey in items_dict:
            item = items_dict[ikey]
            try:
                items.insert_one(item)
            except Exception as error:
                print(error, 'item', item)
        
        for key, d in u['dinos'].items():

            if d.get('status') == 'incubation':
                new_egg(d['incubation_time'], d['egg_id'], u['userid'])
            
            elif d.get('status') == 'dino':

                s = d['stats']
                a = u['activ_items'][key]

                acs = {'game': None, 'collecting': None,
                    'journey': None, 'sleep': None
                    }

                for i in ['game', 'journey']:
                    try:
                        acs[i] = a[i]
                    except: pass

                try:
                    acs['collecting'] = a['hunt']
                except: pass

                try:
                    acs['sleep'] = a['unv']
                except: pass

                if 'dungeon' in d.keys():
                    for key, i in d['dungeon']['equipment'].items():
                        acs[key] = i
                    
                else:
                    acs['armor'] = None
                    acs['weapon'] = None
                
                if 'user_dungeon' in u.keys():
                    if u['user_dungeon']['equipment'] is not None:
                        acs['backpack'] = u['user_dungeon']['equipment']['backpack']
                        u['user_dungeon']['equipment']['backpack'] = None
                    else:
                        acs['backpack'] = None
                else:
                    acs['backpack'] = None

                new_dino(u['userid'], d['dino_id'], 'pass', d['name'], d['quality'], s['heal'], s['eat'], s['game'], s['mood'], s['unv'], acs)
    
        print(f'{n} / {col}')

work(users_list)
print('enddddddddddddddddddddddddddddddddddddddddddd')


management = client.bot.management
products_b = client.bot.products

def new_product(owner_id, item, price, col):

    pr = {
        'owner_id': owner_id,
        'type': 'item_to_money',
        'item': item,
        'price': price,
        'col': col
    }

    return products_b.insert_one(pr)

print('products')

pr = management.find_one({'_id': 'products'})
pr_dict = pr['products'] #type: ignore

trg = len(pr_dict)
a = 0

for user_key in pr_dict.keys():
    print(f'{a} / {trg}')
    a += 1
    
    products = pr_dict[user_key]['products']

    for key, item in products.items():
        new_product(int(user_key), item['item'], item['price'], item['col'])
    
print('wendfg end')

ref = management.find_one({'_id': 'referal_system'})
print(len(ref['codes'])) #type: ignore
