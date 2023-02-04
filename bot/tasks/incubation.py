from bot.taskmanager import add_task
from bot.config import mongo_client, conf
from time import time
from bot.modules.notifications import user_notification
from bot.modules.dinosaur import insert_dino


incubations = mongo_client.tasks.incubation

async def incubation():
    """Проверка инкубируемых яиц
    """
    data = list(incubations.find({'incubation_time': {'$lte': time()}})).copy()

    for egg in data:
        insert_dino(egg['owner_id'], egg['dino_id']) #создаём динозавра
        incubations.delete_one({'_id': egg['_id']}) #удаляем динозавра из инкубаций
        await user_notification(egg['owner_id'], 'incubation_ready') #отправляем уведомления
    
if __name__ != '__main__':
    if conf.active_tasks:
        add_task(incubation, 10.0, 1.0)