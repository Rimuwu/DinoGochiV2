from bot.taskmanager import add_task
from bot.config import mongo_client, conf
from time import time
from bot.modules.notifications import user_notification
from bot.modules.dinosaur import insert_dino
from bot.exec import bot
from bot.modules.data_format import user_name


incubations = mongo_client.tasks.incubation

async def incubation():
    """Проверка инкубируемых яиц
    """
    data = list(incubations.find({'incubation_time': {'$lte': time()}})).copy()

    for egg in data:
        #создаём динозавра
        insert_dino(egg['owner_id'], egg['dino_id'], egg['quality']) 

        #удаляем динозавра из инкубаций
        incubations.delete_one({'_id': egg['_id']}) 

        #отправляем уведомление
        try:
            chat_user = await bot.get_chat_member(egg['owner_id'], egg['owner_id'])
            user = chat_user.user
        except:
            user = None

        if user:
            name = user_name(user)
            await user_notification(egg['owner_id'], 
                        'incubation_ready', user.language_code,user_name=name) 
    
if __name__ != '__main__':
    if conf.active_tasks:
        add_task(incubation, 10.0, 1.0)