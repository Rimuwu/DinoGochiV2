from time import time

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.data_format import seconds_to_str
from bot.modules.notifications import user_notification
from bot.taskmanager import add_task
from bot.modules.localization import t, get_data
from random import randint, choice


users = mongo_client.bot.users
tavern = mongo_client.connections.tavern


async def tavern_quest():
    ...

async def tavern_replic():
    ...

async def tavern_life():
    in_tavern = list(tavern.find({}))
    
    for user in in_tavern:
        if user['time_in'] + 3600 <= int(time()):
            tavern.delete_one({'_id': user['_id']})
            try:
                await bot.send_message(user['userid'], t('tavern_sleep', user['lang']))
            except Exception: pass

        elif randint(1, 10) == 5:
            names = in_tavern.copy()
            names.remove(user)

            if names:
                random_name = choice(names)['name']
                random_replic = choice(get_data('tavern_dialogs', user['lang']))

                text = f'👤 {random_name}: {random_replic}'
                try:
                    await bot.send_message(user['userid'], text)
                except Exception: pass
        elif randint(1, 15) == 5: print('quest')

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(tavern_life, 180.0, 10.0) # 180.0, 10.0