# Чеки, обновляющие информацию о рейтинге или количестве объектов в базе
# Дабы не собирать информацию каждый раз при запросе пользователя
from bot.config import conf, mongo_client
from bot.taskmanager import add_task
from datetime import datetime
from bot.modules.user import max_lvl_xp
from time import time

dinosaurs = mongo_client.bot.dinosaurs
users = mongo_client.bot.users
items = mongo_client.bot.items
statistic = mongo_client.tasks.statistic
management = mongo_client.bot.management

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

async def rayting_check():
    loc_users = list(users.find({}, 
                        {'userid': 1, 'lvl': 1, 'xp': 1, 'coins': 1}))

    coins_list = list(sorted(loc_users, key=lambda x: x['coins'], reverse=True))
    lvl_list = list(sorted(loc_users, key=lambda x: (x['lvl'] - 1) * max_lvl_xp(x['lvl']) + x['xp'], reverse=True))

    coins_ids, lvl_ids = [], []

    for i in coins_list: coins_ids.append(i['userid'])
    for i in lvl_list: lvl_ids.append(i['userid'])

    management.update_one({'_id': 'rayting_coins'}, 
                          {'$set': {'data': coins_list, 'ids': coins_ids}})
    management.update_one({'_id': 'rayting_lvl'}, 
                          {'$set': {'data': lvl_list, 'ids': lvl_ids}})
    management.update_one({'_id': 'rayt_update'}, 
                          {'$set': {'time': int(time())}})

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(rayting_check, 3600, 15.0)
        add_task(statistic_check, 3600, 30.0)