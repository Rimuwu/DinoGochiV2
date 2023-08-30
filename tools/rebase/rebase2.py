import json
import random
import string
import threading
import time
from pprint import pprint

import pymongo
import sys

sys.path.append('../../')

from bot.modules.friends import insert_friend_connect
from bot.modules.item import AddItemToUser
from bot.modules.dinosaur import generation_code, create_dino_connection, incubation_egg

from bot.modules.localization import available_locales

client = pymongo.MongoClient('localhost', 27017)

referals = client.user.referals
users = client.user.users
langs = client.user.lang
dinosaurs = client.dinosaur.dinosaurs
old = client.bot.users

with open('bot/json/items.json', encoding='utf-8') as f: 
    ITEMS = json.load(f)
    
with open('bot/json/old_ids.json', encoding='utf-8') as f: 
    ids = json.load(f)


def new_dino(userid, d_d):
    
    d_d['stats']['energy'] = d_d['stats']['unv']
    del d_d['stats']['unv']
    
    data = {
        'data_id': d_d['dino_id'],
        'alt_id': generation_code(userid),
        
        'status': d_d['activ_status'],
        'name': d_d['name'],
        'quality': d_d['quality'],
        
        'notification': {},
        'stats': d_d['stats'],
        
        'activ_items': {
                'game': None, 'collecting': None,
                'journey': None, 'sleep': None,
                
                'armor': None,  'weapon': None,
                'backpack': None
        },

        'mood': {
            'breakdown': 0, # очки срыва
            'inspiration': 0 # очки воодушевления
        },

        "memory": {
            'games': [],
            'eat': []
        }
    }
    
    if 'dungeon' in d_d:
        for key, value in d_d['dungeon']['equipment']:
            data['activ_items'][key] = value
    
    dinosaurs.insert_one(data)
    
    dino = dinosaurs.find_one({'alt_id': data['alt_id']})
    
    create_dino_connection(dino['_id'], userid)
    

def new_user(user_data):
    userid = user_data['userid']
    coins = user_data['coins']
    lvl = user_data['lvl']
    
    if not users.find_one({'userid': userid}):
        data = {
            'userid': userid,
            
            'last_message_time': 0,
            'last_markup': 'main_menu',
            
            'settings': {
                'notifications': True,
                'last_dino': None, 
                'profile_view': 1,
                'inv_view': [2, 3],
                'my_name': ''
            },
            
            'notifications': [],
            'coins': coins,
            'lvl': lvl[0],
            'xp': lvl[1],
            
            'dungeon': { 
                'quest_ended': 0,
                'dungeon_ended': 0
            }
        }
        users.insert_one(data)
        
        if user_data['language_code'] not in available_locales: lang = 'en'
        else: lang = user_data['language_code']
        langs.insert_one({'userid': userid, 'lang': lang})

        # Друзья
        for i in user_data['friends']['friend_list']:
            insert_friend_connect(userid, i, 'friends')
        
        for i in user_data['friends']['requests']:
            insert_friend_connect(i, userid, 'request')

            # ПРОВЕРИТЬ ЧТО ПРАВИЛЬНО ПЕРЕНЕСЁТСЯ ЗАПРОС
        
        for key, value in user_data['activ_items'].items():
            for i in value:
                if i:
                    user_data['inventory'].append(i)
        
        if 'user_dungeon' in user_data:
            for key, value in user_data['user_dungeon']['equipment'].items():
                for i in value:
                    if i:
                        user_data['inventory'].append(i)
        
        # Инвентарь
        for item in user_data['inventory']:
            new_id = ids[ item['item_id'] ]
            preabil = {}
            
            if 'abilities' in item:
                for key, value in item['abilities'].items():
                    if value <= 0:
                        item['abilities'][key] = 1
                    if value > ITEMS[new_id]['abilities'][key]:
                        item['abilities'][key] = ITEMS[new_id]['abilities'][key]

                preabil = item['abilities']
            
            AddItemToUser(userid, new_id, 1, preabil)
        
        # Dino
        for key, dino in user_data['dinos']:
            if dino['status'] == 'dino':
                new_dino(userid, dino)
            else:
                incubation_egg(int(dino['egg_id']), userid, 
                    int(dino['incubation_time']),
                    dino['quality']
                    )

uss = list(old.find({}))
for user in uss:
    print(user['user_id'])
    new_user(user)