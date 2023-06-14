from datetime import datetime, timezone
from random import choice, randint, choices
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
quests_data = mongo_client.bot.quests

async def tavern_quest(user):
    free_quests = list(quests_data.find({'owner_id': 0}, {'_id': 1}))
    lang = user['lang']

    if quests_data.count_documents({'owner_id': user['userid']}) < 5:
        if free_quests and not randint(0, 3):
            quest_id = choice(free_quests)['_id']
            quests_data.update_one({'_id': quest_id}, {'owner_id': user['userid']})
            text = t('quest.resаmpling', lang)
        else:
            compl = choices([2, 1], [0.25, 0.5])[0]

            quest = create_quest(compl, lang=lang)
            save_quest(quest, user['userid'])
            text = t('quest.new', lang)

        try: await bot.send_message(user['userid'], text)
        except: pass

async def tavern_replic(in_tavern, user):
    names = in_tavern.copy()
    names.remove(user)
    
    game_names = get_data('quests.authors', user['lang'])
    names += game_names

    if names:
        random_name = choice(names)
        if type(random_name) == dict:
            random_name = random_name['name']
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
                await bot.send_message(user['userid'], 
                        t('tavern_sleep', user['lang']))
            except: pass

        elif randint(1, 5) == 5:
            await tavern_replic(in_tavern, user)
        elif randint(1, 5) == 5:
            await tavern_quest(user)

async def quest_managment():
    quests = quests_data.find({})
    now = datetime.now(timezone.utc)

    for quest in quests:
        create = quest['_id'].generation_time
        delta = now - create

        if delta.seconds >= 2592000:
            quests_data.delete_one({'_id': quest['_id']})

        elif int(time()) >= quest['time_end']:
            quest_resampling(quest['_id'])

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(tavern_life, 180.0, 10.0)
        add_task(quest_managment, 240.0, 10.0)