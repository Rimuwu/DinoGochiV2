import random
from random import randint
from bot.exec import bot

from bot.config import conf, mongo_client
from bot.modules.user import experience_enhancement
from bot.taskmanager import add_task
from bot.const import GAME_SETTINGS
from bot.modules.dinosaur import end_collecting
from bot.modules.item import counts_items
from bot.modules.item_tools import check_accessory
from bot.modules.dinosaur import Dino

collecting_task = mongo_client.tasks.collecting
dinosaurs = mongo_client.bot.dinosaurs
dino_owners = mongo_client.connections.dino_owners

random.seed(1)
REPEAT_MINUTS = 2
ENERGY_DOWN = 0.03 * REPEAT_MINUTS
ENERGY_DOWN2 = 0.5 * REPEAT_MINUTS
LVL_CHANCE = 0.125 * REPEAT_MINUTS
COLLECTING_CHANCE = 0.2 * REPEAT_MINUTS

def mutate_dino_stat(dino, key, value):
    st = dino['stats'][key]
    if st + value > 100: value = 100 - st
    elif st + value < 0: value = -st
    
    dinosaurs.update_one({'_id': dino['_id']}, 
                         {'$inc': {f'stats.{key}': value}})

async def stop_collect(coll_data):
    try:
        chat_user = await bot.get_chat_member(coll_data['sended'], coll_data['sended'])
        lang = chat_user.user.language_code
    except: lang = 'en'
    
    items_list = []
    for key, count in coll_data['items'].items():
        items_list += [key] * count
    items_names = counts_items(items_list, lang)
    
    await end_collecting(coll_data['dino_id'], 
                                 coll_data['items'], coll_data['sended'], 
                                 items_names)

async def collecting_process():
    data = list(collecting_task.find({})).copy()

    for coll_data in data:
        if coll_data['now_count'] >= coll_data['max_count']:
            await stop_collect(coll_data)
        else:
            if random.uniform(0, 1) <= ENERGY_DOWN:
                if random.uniform(0, 1) <= ENERGY_DOWN2: 
                    dino = dinosaurs.find_one({'_id': coll_data['dino_id']})
                    mutate_dino_stat(dino, 'energy', -1)
            
            dino = Dino(coll_data['dino_id'])
            if check_accessory(dino, '15', True): chance = 0.25
            else: chance = 0.2
            
            if random.uniform(0, 1) <= chance: 
                await experience_enhancement(coll_data['sended'], 
                                             randint(1, 5))

            if random.uniform(0, 1) <= COLLECTING_CHANCE:
                items = GAME_SETTINGS['collecting_items'][coll_data["collecting_type"]]
                count = randint(1, 3)
                
                if coll_data['now_count'] + count > coll_data['max_count']:
                    count = coll_data['max_count'] - coll_data['now_count']
                
                for _ in range(count):
                    rar = random.choices(list(items.keys()), [50, 25, 15, 9, 1])[0]
                    item = random.choice(items[rar])

                    if item in coll_data['items']:
                        coll_data['items'][item] += 1
                    else: coll_data['items'][item] = 1
                
                collecting_task.update_one({'_id': coll_data['_id']}, 
                                            {'$set': {
                                                'items': coll_data['items']
                                                    },
                                            '$inc': {'now_count': count}
                                                })
                    
                if coll_data['now_count'] + count == coll_data['max_count']:
                    await stop_collect(coll_data)
                
                
if __name__ != '__main__':
    if conf.active_tasks:
        add_task(collecting_process, REPEAT_MINUTS * 60.0, 1.0)