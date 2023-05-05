from time import time

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.data_format import user_name
from bot.modules.dinosaur import insert_dino
from bot.modules.notifications import user_notification
from bot.taskmanager import add_task
from bot.modules.mood import mood_while_if
from bot.modules.dinosaur import Dino, edited_stats
from random import randint
import random
from bot.modules.user import experience_enhancement

game_task = mongo_client.tasks.game
dinosaurs = mongo_client.bot.dinosaurs
dino_owners = mongo_client.connections.dino_owners

random.seed(1)
REPEAT_MINUTS = 2
ENERGY_DOWN = 0.007 * REPEAT_MINUTS
LVL_CHANCE = 0.125 * REPEAT_MINUTS
GAME_CHANCE = 0.17 * REPEAT_MINUTS

async def game_end():
    data = list(game_task.find({'game_end': 
        {'$lte': int(time())}})).copy()

    for i in data:
        dino = dinosaurs.find_one({'_id': i['dino_id']})
        if dino:
            dinosaurs.update_one({'_id': i['dino_id']}, 
                                 {'$set': {'status': 'pass'}})

            #отправляем уведомление
            try:
                chat_user = await bot.get_chat_member(dino['owner_id'], dino['owner_id'])
                user = chat_user.user
            except: user = None

            if user:
                name = user_name(user)
                await user_notification(dino['owner_id'], 
                            'game_end', user.language_code, 
                            user_name=name, 
                            dino_alt_id_markup=dino['owner_id']['alt_id'])

            mood_while_if(i['dino_id'], 'end_game', 'game', 40, 101)

        game_task.delete_one({'_id': i['_id']}) 

async def game_process():
    data = list(game_task.find({'game_end': {'$gte': int(time())}})).copy()
    
    for game_data in data:
        percent = game_data['game_percent']
        dino = dinosaurs.find_one({'_id': game_data['dino_id']})
        
        if dino:
            if random.uniform(0, 1) <= ENERGY_DOWN:
                energy_stat = randint(-1, 0)
    
            if dino.stats['game'] < 100:
                if random.uniform(0, 1) <= LVL_CHANCE: 
                    
                    dino_con = dino_owners.find_one({'dino_id': dino._id})
                    if dino_con:
                        userid = dino_con['owner_id']
                        await experience_enhancement(userid, randint(0, 20))
                
                if dino.stats['game'] < 100:
                    if random.uniform(0, 1) <= GAME_CHANCE:
                        game_stat = edited_stats(dino.stats['game'], 
                                            int(randint(2, 10) * percent))

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(game_end, REPEAT_MINUTS * 60.0, 1.0)
        add_task(game_process, REPEAT_MINUTS * 60.0, 1.0)