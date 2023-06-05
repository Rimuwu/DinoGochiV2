import random
from random import randint
from bot.exec import bot

from bot.config import conf, mongo_client
from bot.modules.user import experience_enhancement
from bot.taskmanager import add_task
from bot.const import GAME_SETTINGS
from bot.modules.dinosaur import end_collecting
from bot.modules.item import counts_items
from bot.modules.accessory import check_accessory
from bot.modules.dinosaur import Dino, mutate_dino_stat
from bot.modules.mood import check_inspiration

collecting_task = mongo_client.tasks.collecting
dinosaurs = mongo_client.bot.dinosaurs
dino_owners = mongo_client.connections.dino_owners

REPEAT_MINUTS = 2


if __name__ != '__main__':
    if conf.active_tasks: ...
        # add_task(, REPEAT_MINUTS * 60.0, 1.0)