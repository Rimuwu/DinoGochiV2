from time import time

from bson.objectid import ObjectId

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.data_format import seconds_to_str
from bot.modules.notifications import dino_notification
from bot.taskmanager import add_task

sleepers = mongo_client.tasks.sleep
dinosaurs = mongo_client.bot.dinosaurs

LONG_SLEEP_COLDOWN_MIN = 6
LONG_SLEEP_TIME_MIN = 600
LONG_MAX_UNIT_AFTER = LONG_SLEEP_TIME_MIN // LONG_SLEEP_COLDOWN_MIN
LONG_ONE_TIME = LONG_MAX_UNIT_AFTER // 100

SHORT_SLEEP_COLDOWN_MIN = LONG_SLEEP_COLDOWN_MIN // 2
SHORT_SLEEP_TIME_MIN = LONG_SLEEP_TIME_MIN // 2
SHORT_MAX_UNIT_AFTER = SHORT_SLEEP_TIME_MIN // SHORT_SLEEP_COLDOWN_MIN
SHORT_ONE_TIME = SHORT_MAX_UNIT_AFTER // 100


async def end_sleep(dinoid: ObjectId, sleeperid: ObjectId, sec_time: int):
    dinosaurs.update_one({'_id': dinoid}, {'$set': {'status': 'pass'}})
    sleepers.delete_one({'_id': sleeperid})

    await dino_notification(dinoid, 'sleep_end', 
                            add_time_end=True,
                            secs=sec_time)

async def one_time(data, one_time_unit):
    for sleeper in data:
        add_energy, sec_time = 0, 0
        dino = dinosaurs.find_one({'_id': sleeper['dino_id']})

        if sleeper['sleep_type'] == 'long':
            sec_time = int(time()) - sleeper['sleep_start']
        elif sleeper['sleep_type'] == 'short':
            sec_time = sleeper['sleep_end'] - sleeper['sleep_start']

        if dino:
            energy = dino['stats']['energy']
            if energy >= 100:
                await end_sleep(dino['_id'], sleeper['_id'], sec_time)
            else:
                if energy + one_time_unit >= 100:
                    add_energy = 100 - energy
                    await end_sleep(dino['_id'], sleeper['_id'], sec_time)
                else:
                    add_energy = one_time_unit
                dinosaurs.update_one({'_id': dino['_id']}, {'$inc': {'stats.energy': add_energy}})
        else:
            sleepers.delete_one({"_id": sleeper['_id']})

async def short_check_notification():
    """Уведомления и окончание короткого сна

    """
    data = list(sleepers.find({'sleep_type': 'short', 
                               'sleep_end': {'$lte': int(time())}
                             })).copy()

    for sleeper in data:
        dino = dinosaurs.find_one({'_id': sleeper['dino_id']})
        if dino:
            await end_sleep(dino['_id'], sleeper['_id'], 
                            sleeper['sleep_end'] - sleeper['sleep_start'])

async def short_check():
    data = list(sleepers.find({'sleep_type': 'short'})).copy()
    await one_time(data, LONG_ONE_TIME)

async def long_check():
    data = list(sleepers.find({'sleep_type': 'long'})).copy()
    await one_time(data, SHORT_ONE_TIME)

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(long_check, LONG_SLEEP_COLDOWN_MIN * 60, 1.0)
        add_task(short_check, SHORT_SLEEP_COLDOWN_MIN * 60, 1.0)
        add_task(short_check_notification, 30, 1.0)