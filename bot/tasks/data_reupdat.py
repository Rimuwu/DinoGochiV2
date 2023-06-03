# Чеки, обновляющие информацию о рейтинге или количестве объектов в базе
# Дабы не собирать информацию каждый раз при запросе пользователя
from bot.config import conf, mongo_client
from bot.taskmanager import add_task
from datetime import datetime

dinosaurs = mongo_client.bot.dinosaurs
users = mongo_client.bot.users
items = mongo_client.bot.items
statistic = mongo_client.tasks.statistic

# Чек статистики, запускать раз в час
async def statistic_check():
    
    items_len = items.count_documents({})
    users_len = users.count_documents({})
    dinosaurs_len = dinosaurs.count_documents({})
    
    dinosaurs.count_documents({})
    
    data = {
        'date': str(datetime.now().date()),
        'dinosaurs': dinosaurs_len,
        'users': users_len,
        'items': items_len
    }
    if res := statistic.find_one({'date': data['date']}):
        statistic.delete_one({'_id': res['_id']})

    statistic.insert_one(data)

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(statistic_check, 3600, 30.0)