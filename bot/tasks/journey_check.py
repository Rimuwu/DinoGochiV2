import random
from random import randint
from time import time

from bot.config import conf, mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.handlers.actions.journey import send_logs
from bot.modules.accessory import check_accessory
from bot.modules.dinosaur import (Dino, end_collecting, end_journey,
                                  get_dino_language, mutate_dino_stat)
from bot.modules.item import counts_items
from bot.modules.journey import random_event
from bot.modules.quests import quest_process
from bot.modules.user import experience_enhancement
from bot.taskmanager import add_task

journey = mongo_client.tasks.journey
dinosaurs = mongo_client.bot.dinosaurs
dino_owners = mongo_client.connections.dino_owners

REPEAT_MINUTS = 3
EVENT_CHANCE = 0.17 * REPEAT_MINUTS

async def end_journey_time():
    data = list(journey.find({'journey_end': {'$lte': int(time())}})).copy()
    for i in data:
        dino = dinosaurs.find_one({'_id': i['dino_id']})
        if dino:
            end_journey(i['dino_id'])
            quest_process(i['sended'], 'journey', i['journey_end'] - i['journey_start'])

            lang = await get_dino_language(i['dino_id'])
            await send_logs(i['sended'], lang, i, dino['name'])

async def events():
    data = list(journey.find({'journey_end': {'$gte': int(time())}})).copy()

    for i in data:
        if random.uniform(0, 1) <= EVENT_CHANCE:
            await random_event(i['dino_id'], i['location'])

if __name__ != '__main__':
    if conf.active_tasks: 
        add_task(end_journey_time, 60.0, 5.0)
        add_task(events, REPEAT_MINUTS * 60.0, 20.0)