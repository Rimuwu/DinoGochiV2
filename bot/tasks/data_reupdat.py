# Чеки, обновляющие информацию о рейтинге или количестве объектов в базе
# Дабы не собирать информацию каждый раз при запросе пользователя
from bot.config import conf, mongo_client
from bot.taskmanager import add_task
from datetime import datetime
from bot.modules.user import max_lvl_xp
from time import time
from bot.modules.notifications import user_notification
from bot.modules.dinosaur import get_owner, get_dino_language

dinosaurs = mongo_client.dinosaur.dinosaurs
users = mongo_client.user.users
items = mongo_client.items.items
statistic = mongo_client.other.statistic
management = mongo_client.other.management
kindergarten = mongo_client.dino_activity.kindergarten

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

async def kindergarten_update():
    data = list(kindergarten.find({'type': 'save',
                                   'end': {'$lte': int(time())}})
                ).copy()

    for i in data: kindergarten.delete_one({'_id': i['_id']})

async def dino_kindergarten():
    data = list(kindergarten.find({'type': 'dino',
                                   'end': {'$lte': int(time())}})
                ).copy()

    for i in data: 
        dinosaurs.update_one({'_id': i['dinoid']}, {'$set': {'status': 'pass'}})
        kindergarten.delete_one({'_id': i['_id']})

        dino = dinosaurs.find_one({'_id': i['dinoid']})
        if dino:
            owner = get_owner(i['dinoid'])
            if owner:
                lang = get_dino_language(i['dinoid'])
                await user_notification(owner['owner_id'], 'kindergarten', lang, 
                                dino_name=dino['name'], 
                                dino_alt_id_markup=dino['alt_id'])

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(rayting_check, 3600, 15.0)
        add_task(statistic_check, 3600, 30.0)
        add_task(dino_kindergarten, 1800, 15.0)
        add_task(kindergarten_update, 43200, 30.0)