from bot.config import conf, mongo_client
from bot.taskmanager import add_task
from bot.modules.events import auto_event, create_event, add_event
from time import time
from random import randint
from bot.modules.logs import log

events = mongo_client.tasks.events

async def old_events():
    """ Удаляет истёкшие события
    """
    events_data = list(events.find({}, {'type': 1, 'time_end': 1})).copy()

    for i in events_data:
        if i['time_end'] != 0 and int(time()) >= i['time_end']:
            events.delete_one({'type': i['type']})

async def random_event():
    events_data = list(events.find({}, {'type'})).copy()
    not_system = []
    
    for i in events_data:
        if i['type'] not in ['new_year', 'time_year']: not_system.append(i['type'])

    if (True or randint(1, 18) == 18) and len(not_system ) == 0:
        event = create_event()
        add_event(event)
        log(f'Создано событие - {event}')

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(auto_event, 3600, 5.0)
        add_task(old_events, 240, 1.0)
        add_task(random_event, 3600, 1.0)