import random
from random import randint
from time import time

from bot.config import conf, mongo_client
from bot.modules.mood import add_mood
from bot.modules.notifications import dino_notification
from bot.modules.user import experience_enhancement
from bot.taskmanager import add_task

game_task = mongo_client.tasks.game
dinosaurs = mongo_client.bot.dinosaurs
dino_owners = mongo_client.connections.dino_owners

random.seed(1)
REPEAT_MINUTS = 2
ENERGY_DOWN = 0.03 * REPEAT_MINUTS
ENERGY_DOWN2 = 0.5 * REPEAT_MINUTS
LVL_CHANCE = 0.125 * REPEAT_MINUTS
GAME_CHANCE = 0.17 * REPEAT_MINUTS

def mutate_dino_stat(dino, key, value):
    st = dino['stats'][key]
    if st + value > 100: value = 100 - st
    elif st + value < 0: value = -st
    
    dinosaurs.update_one({'_id': dino['_id']}, 
                         {'$inc': {f'stats.{key}': value}})

async def game_end():
    data = list(game_task.find({'game_end': 
        {'$lte': int(time())}})).copy()

    for i in data:
        dino = dinosaurs.find_one({'_id': i['dino_id']})
        if dino:
            dinosaurs.update_one({'_id': i['dino_id']}, 
                                 {'$set': {'status': 'pass'}})

            await dino_notification(i['dino_id'], 'game_end')
            add_mood(i['dino_id'], 'end_game', 
                     randint(1, 2), int(10800 * i['game_percent'])
                     )

        game_task.delete_one({'_id': i['_id']}) 

async def game_process():
    data = list(game_task.find({'game_end': {'$gte': int(time())}})).copy()
    
    for game_data in data:
        percent = game_data['game_percent']
        dino = dinosaurs.find_one({'_id': game_data['dino_id']})
        
        if dino:
            if random.uniform(0, 1) <= ENERGY_DOWN:
                if random.uniform(0, 1) <= ENERGY_DOWN2: 
                    mutate_dino_stat(dino, 'energy', -1)
    
            if dino['stats']['game'] < 100:
                if random.uniform(0, 1) <= LVL_CHANCE: 
                    
                    dino_con = dino_owners.find_one({'dino_id': dino['_id']})
                    if dino_con:
                        userid = dino_con['owner_id']
                        await experience_enhancement(userid, randint(0, 20))
                
                if dino['stats']['game'] < 100:
                    if random.uniform(0, 1) <= GAME_CHANCE:
                        mutate_dino_stat(dino, 'game', int(randint(2, 10) * percent))

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(game_end, REPEAT_MINUTS * 60.0, 1.0)
        add_task(game_process, REPEAT_MINUTS * 60.0, 1.0)