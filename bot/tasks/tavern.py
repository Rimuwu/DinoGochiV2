from datetime import datetime, timezone
from random import choice, randint
from time import time

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.data_format import seconds_to_str
from bot.modules.localization import get_data, t
from bot.modules.notifications import user_notification
from bot.modules.quests import create_quest, quest_resampling, save_quest
from bot.taskmanager import add_task

users = mongo_client.bot.users
tavern = mongo_client.connections.tavern
quests_data = mongo_client.connections.quests


async def tavern_quest(user):
    free_quests = list(quests_data.find({'owner_id': 0}, {'_id': 1}))

    if free_quests and not randint(0, 3):
        quest_id = choice(free_quests)['_id']
        quests_data.update_one({'_id': quest_id})
    else:
        quest = create_quest()
        save_quest(quest, user['userid'])
    

async def tavern_replic(in_tavern, user):
    names = in_tavern.copy()
    names.remove(user)

    if names:
        random_name = choice(names)['name']
        random_replic = choice(get_data('tavern_dialogs', user['lang']))

        text = f'👤 {random_name}: {random_replic}'
        try:
            await bot.send_message(user['userid'], text)
        except Exception: pass

async def tavern_life():
    in_tavern = list(tavern.find({}))
    
    for user in in_tavern:
        if user['time_in'] + 3600 <= int(time()):
            tavern.delete_one({'_id': user['_id']})
            try:
                await bot.send_message(user['userid'], t('tavern_sleep', user['lang']))
            except Exception: pass

        elif randint(1, 10) == 5:
            await tavern_replic(in_tavern, user)

        elif randint(1, 10) == 5:  await tavern_quest(user)

async def quest_managment():
    quests = quests_data.find({})
    now = datetime.now(timezone.utc)

    for quest in quests:
        create = quest['_id'].generation_time
        delta = now - create

        if delta.secodnds >= 2592000:
            quests_data.delete_one({'_id': quest['_id']})

        elif int(time()) >= quest['time_end']:
            quest_resampling(quest['_id'])

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(tavern_life, 180.0, 10.0) # 180.0, 10.0
        add_task(tavern_life, 120.0, 10.0)