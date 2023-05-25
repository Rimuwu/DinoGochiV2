from bot.config import conf, mongo_client
from bot.modules.notifications import notification_manager
from bot.taskmanager import add_task

dinosaurs = mongo_client.bot.dinosaurs
REPEAT_MINUTS = 5

async def dino_notifications():
    dinos = dinosaurs.find({})
    for dino in dinos:
        dino_id = dino['_id']
        for stat in dino['stats']:
            
            unit = dino['stats'][stat]
            await notification_manager(dino_id, stat, unit)

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(dino_notifications, REPEAT_MINUTS * 60.0, 15.0)