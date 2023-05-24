from bot.config import conf, mongo_client
from bot.modules.notifications import (check_dino_notification, critical_line,
                                       dino_notification,
                                       dino_notification_delete)
from bot.taskmanager import add_task

dinosaurs = mongo_client.bot.dinosaurs
REPEAT_MINUTS = 5

async def dino_notifications():
    dinos = dinosaurs.find({})
    for dino in dinos:
        dino_id = dino['_id']
        for stat in dino['stats']:
            unit = dino['stats'][stat]

            if critical_line[stat] >= unit:
                if check_dino_notification(dino_id, f'need_{stat}', False):
                    # Отправка уведомления
                    await dino_notification(dino_id, f'need_{stat}', unit=unit)

            elif unit >= critical_line[stat] + 20:
                # Удаляем уведомление 
                dino_notification_delete(dino_id, f'need_{stat}')

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(dino_notifications, REPEAT_MINUTS * 60.0, 15.0)