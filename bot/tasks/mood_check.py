from time import time

from bot.config import conf, mongo_client
from bot.modules.dinosaur import mutate_dino_stat
from bot.taskmanager import add_task

dino_mood = mongo_client.connections.dino_mood
dinosaurs = mongo_client.bot.dinosaurs

REPEAT_MINUTS = 5

async def mood_check():
    """ Проверяет и выдаёт настроение
    """
    
    res = list(dino_mood.find({}))
    upd_data = {}
    
    for mood_data in res:
        dino_id = mood_data['dino_id']
        
        if dino_id in upd_data:
            upd_data[dino_id] += mood_data['unit']
        else: upd_data[dino_id] = mood_data['unit']
        
        if mood_data['type'] == 'mood_edit':
            
            if int(time()) >= mood_data['end_time']:
                # Закончилось время эффекта
                dino_mood.delete_one({'_id': mood_data['_id']})

        elif mood_data['type'] == 'mood_while':
            while_data = mood_data['while']
            char = while_data['characteristic']
            dino = dinosaurs.find_one({'_id': mood_data['dino_id']})
            
            if dino:
                if while_data['min_unit'] >= dino['stats'][char] or \
                    dino['stats'][char] >= while_data['max_unit']:
                        dino_mood.delete_one({'_id': mood_data['_id']})
    
    for dino_id, unit in upd_data.items():
        dino = dinosaurs.find_one({'_id': dino_id})
        if dino: await mutate_dino_stat(dino, 'mood', unit)

    print(upd_data)

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(mood_check, REPEAT_MINUTS, 5.0) # * 60.0