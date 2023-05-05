from time import time

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.data_format import user_name
from bot.modules.dinosaur import insert_dino
from bot.modules.notifications import user_notification
from bot.taskmanager import add_task

incubations = mongo_client.tasks.incubation

async def incubation():
    """Проверка инкубируемых яиц
    """
    data = list(incubations.find({'incubation_time': {'$lte': int(time())}})).copy() #$lte - incubation_time <= time()

    for egg in data:
        #создаём динозавра
        res, alt_id = insert_dino(egg['owner_id'], egg['dino_id'], egg['quality']) 

        #удаляем динозавра из инкубаций
        incubations.delete_one({'_id': egg['_id']}) 

        #отправляем уведомление
        try:
            chat_user = await bot.get_chat_member(egg['owner_id'], egg['owner_id'])
            user = chat_user.user
        except: user = None

        if user:
            name = user_name(user)
            await user_notification(egg['owner_id'], 
                        'incubation_ready', user.language_code, 
                        user_name=name, dino_alt_id_markup=alt_id) 
    
if __name__ != '__main__':
    if conf.active_tasks:
        add_task(incubation, 5.0, 1.0)