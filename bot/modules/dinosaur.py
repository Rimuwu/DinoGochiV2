import asyncio
import datetime
from datetime import datetime, timezone
from random import choice, randint
from time import time

from bson.objectid import ObjectId

from bot.config import mongo_client
from bot.const import DINOS, GAME_SETTINGS
from bot.modules.data_format import random_code, random_quality
from bot.modules.images import create_dino_image, create_egg_image
from bot.modules.item import AddItemToUser
from bot.modules.localization import log
from bot.modules.notifications import (dino_notification, notification_manager,
                                       user_notification)
from bot.const import GAME_SETTINGS as GS

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs
incubations = mongo_client.tasks.incubation
dino_owners = mongo_client.connections.dino_owners
dead_dinos = mongo_client.bot.dead_dinos

game_task = mongo_client.tasks.game
sleep_task = mongo_client.tasks.sleep
journey_task = mongo_client.tasks.journey
collecting_task = mongo_client.tasks.collecting

class Dino:

    def __init__(self, baseid: ObjectId):
        """Создание объекта динозавра."""
        self._id = baseid

        self.data_id = 0
        self.alt_id = 'alt_id' #альтернативный id 

        self.status = 'pass' # game, journey, sleep, collecting, dungeon...
        self.name = 'name'
        self.quality = 'com'
        
        self.notifications = {}

        self.stats = {
                'heal': 10, 'eat': 10,
                'game': 10, 'mood': 10,
                'energy': 10
        }

        self.activ_items = {
                'game': None, 'collecting': None,
                'journey': None, 'sleep': None,
                
                'armor': None,  'weapon': None,
                'backpack': None
        }

        self.mood = {
            'breakdown': 0, # очки срыва
            'inspiration': 0 # очки воодушевления
        }

        self.memory = {
            'games': [],
            'eat': []
        }

        find_result = dinosaurs.find_one({"_id": self._id})
        if not find_result:
            find_result = dinosaurs.find_one({"alt_id": self._id})
        if find_result:
            self.UpdateData(find_result)

    def UpdateData(self, data):
        if data: self.__dict__ = data
        
    def __str__(self) -> str:
        return self.name

    def update(self, update_data: dict):
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        data = dinosaurs.update_one({"_id": self._id}, update_data)
        # self.UpdateData(data) #Не получается конвертировать в словарь возвращаемый объект
        self.UpdateData(dinosaurs.find_one({"alt_id": self._id}))
        if self.stats['heal'] <= 0: self.dead()

    def delete(self):
        """ Удаление всего, что связано с дино
        """
        dinosaurs.delete_one({'_id': self._id})
        for collection in [game_task, sleep_task, journey_task, 
                           collecting_task, dino_owners]:
            collection.delete_many({'dino_id': self._id})

    def dead(self):
        """ Это очень грустно, но необходимо...
            Удаляем объект динозавра, отсылает уведомление и сохраняет динозавра в мёртвых
        """
        owner = self.get_owner

        if owner:
            user = users.find_one({"userid": owner['owner_id']})

            save_data = {
                'data_id': self.data_id,
                'quality': self.quality,
                'name': self.name,
                'owner_id': owner['owner_id']
            }
            dead_dinos.insert_one(save_data)

            for key, item in self.activ_items.items():
                if item: AddItemToUser(owner['owner_id'], item['item_id'])

            if user:
                
                col_dinos = dino_owners.find_one(
                    {'onwer_id': owner['owner_id']})
                
                col_eggs = incubations.find_one(
                    {'onwer_id': owner['owner_id'], 'type': owner})

                if user['lvl'] <= GS['dead_dialog_max_lvl'] and not col_dinos and not col_eggs:
                    way = 'not_independent_dead'
                else:
                    way = 'independent_dead'
                    AddItemToUser(user['userid'], GS['dead_dino_item'])

                asyncio.run_coroutine_threadsafe(
                    user_notification(owner['owner_id'], way, 
                            dino_name=self.name), asyncio.get_event_loop())
        self.delete()

    def image(self, profile_view: int=1, custom_url: str=''):
        """Сгенерировать изображение объекта
        """
        return create_dino_image(self.data_id, self.stats, self.quality, profile_view, self.age.days, custom_url)

    def collecting(self, owner_id: int, coll_type: str, max_count: int):
        return start_collecting(self._id, owner_id, coll_type, max_count)
    
    def game(self, duration: int=1800, percent: int=1):
        return start_game(self._id, duration, percent)
    
    def journey(self, owner_id: int, duration: int=1800):
        return start_journey(self._id, owner_id, duration)
    
    def sleep(self, s_type: str='long', duration: int=1):
        return start_sleep(self._id, s_type, duration)
    
    def memory_percent(self, memory_type: str, obj: str, update: bool = True):
        """memory_type - games / eat
        
           Сохраняет в памяти объект и выдаёт процент.
           Сохраняет только при update = True
        """
        repeat = self.memory[memory_type].count(obj)
        percent = GAME_SETTINGS['penalties'][memory_type][str(repeat)]

        if update:
            max_repeat = {'games': 3, 'eat': 5}

            if len(self.memory[memory_type]) < max_repeat[memory_type]:
                self.update({'$push': {f'memory.{memory_type}': obj}})
            else:
                self.memory[memory_type].pop()
                self.memory[memory_type].insert(0, obj)
                self.update({'$set': 
                    {f'memory.{memory_type}': self.memory[memory_type]}}
                            )
        return percent, repeat

    @property
    def data(self): return get_dino_data(self.data_id)

    @property
    def age(self): return get_age(self._id)
    
    @property
    def get_owner(self): return get_owner(self._id)


class Egg:

    def __init__(self, baseid: ObjectId):
        """Создание объекта яйца."""
        
        self._id = baseid
        self.incubation_time = 0
        self.egg_id = 0
        self.owner_id = 0
        self.quality = 'random'
        self.dino_id = 0

        self.UpdateData(incubations.find_one({"_id": self._id}))

    def UpdateData(self, data):
        if data:
            self.__dict__ = data

    def __str__(self) -> str:
        return f'{self._id} {self.quality}'

    def update(self, update_data: dict):
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        data = incubations.update_one({"_id": self._id}, update_data)
        # self.UpdateData(data) #Не получается конвертировать в словарь возвращаемый объект
    
    def delete(self):
        incubations.delete_one({'_id': self._id})


    def image(self, lang: str='en'):
        """Сгенерировать изображение объекта.
        """
        t_inc = self.remaining_incubation_time()
        return create_egg_image(egg_id=self.egg_id, rare=self.quality, seconds=t_inc, lang=lang)
    
    def remaining_incubation_time(self):
        return self.incubation_time - int(time())


def get_dino_data(data_id: int):
    data = {}
    try:
        data = DINOS['elements'][str(data_id)]
    except Exception as e:
        log(f'Ошибка в получении данных динозавра -> {e}', 3)
    return data

def random_dino(quality: str='com') -> int:
    """Рандомизация динозавра по редкости
    """
    return choice(DINOS[quality])
    
def incubation_egg(egg_id: int, owner_id: int, inc_time: int=0, quality: str='random', dino_id: int=0):
    """Создание инкубируемого динозавра
    """
    egg = Egg(ObjectId())
    
    egg.incubation_time = inc_time + int(time())
    egg.egg_id = egg_id
    egg.owner_id = owner_id
    egg.quality = quality
    egg.dino_id = dino_id

    if inc_time == 0: #Стандартное время инкцбации 
        egg.incubation_time = int(time()) + GAME_SETTINGS['first_dino_time_incub']
    
    log(prefix='InsertEgg', message=f'owner_id: {owner_id} data: {egg.__dict__}', lvl=0)
    return incubations.insert_one(egg.__dict__)

def create_dino_connection(dino_baseid: ObjectId, owner_id: int, con_type: str='owner'):
    """ Создаёт связь в базе между пользователем и динозавром
        con_type = owner / add_owner
    """

    assert con_type in ['owner', 'add_owner'], f'Неподходящий аргумент {con_type}'

    con = {
        'dino_id': dino_baseid,
        'owner_id': owner_id,
        'type': con_type
    }

    log(prefix='CreateConnection', 
        message=f'Dino - Owner Data: {con}', 
        lvl=0)
    return dino_owners.insert_one(con)

def insert_dino(owner_id: int=0, dino_id: int=0, quality: str='random'):
    """Создания динозавра в базе
       + связь с владельцем если передан owner_id 
    """
    
    def generation_code(owner_id):
        code = f'{owner_id}_{random_code(8)}'
        if dinosaurs.find_one({'alt_id': code}):
            code = generation_code(owner_id)
        return code

    if quality in ['random', 'rar']: quality = random_quality()
    if not dino_id: dino_id = random_dino(quality)

    dino_data = get_dino_data(dino_id)
    dino = Dino(ObjectId())
    
    dino.data_id = dino_id
    dino.alt_id = generation_code(owner_id)
    dino.name = dino_data['name']
    dino.quality = quality or dino_data['quality']
    dino.stats = {
        'heal': 100, 'eat': randint(70, 100),
        'game': randint(30, 90), 'mood': randint(30, 100),
        'energy': randint(80, 100)
        }
    
    log(prefix='InsertDino', 
        message=f'owner_id: {owner_id} dino_id: {dino_id} name: {dino.name} quality: {dino.quality}', 
        lvl=0)

    result = dinosaurs.insert_one(dino.__dict__)
    if owner_id != 0:
        # Создание связи, если передан id владельца
        create_dino_connection(result.inserted_id, owner_id)

    return result, dino.alt_id


def start_game(dino_baseid: ObjectId, duration: int=1800, 
               percent: float=1):
    """Запуск активности "игра". 
       + Изменение статуса динозавра 
    """

    game = {
        'dino_id': dino_baseid,
        'game_start': int(time()),
        'game_end': int(time()) + duration,
        'game_percent': percent
    }
    result = game_task.insert_one(game)
    dinosaurs.update_one({"_id": dino_baseid}, 
                         {'$set': {'status': 'game'}})
    return result

async def end_game(dino_id: ObjectId, send_notif: bool=True):
    """Заканчивает игру и отсылает уведомление.
    """
    
    dinosaurs.update_one({'_id': dino_id}, 
                            {'$set': {'status': 'pass'}})
    game_task.delete_one({'dino_id': dino_id}) 
    
    if send_notif: await dino_notification(dino_id, 'game_end')


def start_sleep(dino_baseid: ObjectId, s_type: str='long', 
                duration: int=1):
    """Запуск активности "сон". 
       + Изменение статуса динозавра 
    """

    assert s_type in ['long', 'short'], f'Неподходящий аргумент {s_type}'

    sleep = {
        'dino_id': dino_baseid,
        'sleep_start': int(time()),
        'sleep_type': s_type
    }
    if s_type == 'short':
        sleep['sleep_end'] = int(time()) + duration

    result = sleep_task.insert_one(sleep)
    dinosaurs.update_one({"_id": dino_baseid}, 
                         {'$set': {'status': 'sleep'}})
    return result

async def end_sleep(dino_id: ObjectId,
                    sec_time: int=0, send_notif: bool=True):
    """Заканчивает сон и отсылает уведомление.
       sec_time - время в секундах, сколько спал дино.
    """
    sleep_task.delete_one({'dino_id': dino_id})

    dinosaurs.update_one({'_id': dino_id}, 
                         {'$set': {'status': 'pass'}})
    if send_notif:
        await dino_notification(dino_id, 'sleep_end', 
                            add_time_end=True,
                            secs=sec_time)


def start_journey(dino_baseid: ObjectId, owner_id: int, duration: int=1800):
    """Запуск активности "путешествие". 
       + Изменение статуса динозавра 
    """

    game = {
        'sended': owner_id, # Так как у нас может быть несколько владельцев
        'dino_id': dino_baseid,
        'journey_start': int(time()),
        'journey_end': int(time()) + duration,
        'journey_log': [],
        'items': [],
        'coins': 0
    }
    result = journey_task.insert_one(game)
    dinosaurs.update_one({"_id": dino_baseid}, 
                         {'$set': {'status': 'journey'}})
    return result


def start_collecting(dino_baseid: ObjectId, owner_id: int, coll_type: str, max_count: int):
    """Запуск активности "сбор пищи". 
       + Изменение статуса динозавра 
    """

    assert coll_type in ['collecting', 'hunt', 'fishing', 'all'], f'Неподходящий аргумент {coll_type}'

    game = {
        'sended': owner_id, # Так как у нас может быть несколько владельцев
        'dino_id': dino_baseid,
        'collecting_type': coll_type,
        'max_count': max_count,
        'now_count': 0,
        'items': {}
    }
    result = collecting_task.insert_one(game)
    dinosaurs.update_one({"_id": dino_baseid}, 
                         {'$set': {'status': 'collecting'}})
    return result

async def end_collecting(dino_id: ObjectId, items: dict, recipient: int,
                         items_names: str,
                         send_notif: bool = True):
    """Конец сбора пищи,
       items_name - сгенерированное сообщение для уведолмения
       items - словарь типа {'id': count: int} с предметами для добавления
       recipient - тот кто получит собранные предметы
    """

    collecting_task.delete_one({'dino_id': dino_id})
    dinosaurs.update_one({'_id': dino_id}, 
                        {'$set': {'status': 'pass'}})

    for key_id, count in items.items():
        AddItemToUser(recipient, key_id, count)

    if send_notif:
        await dino_notification(dino_id, 'end_collecting', items_names=items_names)

def edited_stats(before: int, unit: int):
    """ Лёгкая функция проверки на 
        0 <= unit <= 100 
    """
    after = 0
    if before + unit > 100: after = 100
    elif before + unit < 0: after = 0
    else: after = before + unit

    return after

def get_age(dinoid: ObjectId):
    """.seconds .days
    """
    dino_create = dinoid.generation_time
    now = datetime.now(timezone.utc)
    delta = now - dino_create
    return delta

async def mutate_dino_stat(dino: dict, key: str, value: int):
    st = dino['stats'][key]
    now = st + value
    if now > 100: value = 100 - st
    elif now < 0: value = -st

    if key == 'heal' and now <= 0:
        Dino(dino['_id']).dead()
    else:
        await notification_manager(dino['_id'], key, now)
        dinosaurs.update_one({'_id': dino['_id']}, 
                            {'$inc': {f'stats.{key}': value}})
        
def get_owner(dino_id: ObjectId):
    return dino_owners.find_one({'dino_id': dino_id, 'type': 'owner'})

def set_status(dino_id: ObjectId, new_status: str):
    """ Устанавливает состояние динозавра.
    """

    assert new_status in ['pass', 'sleep', 'game', 'journey', 'collecting', 'dungeon', 'freezing', 'kindergarten', 'hysteria'], f'Состояние {new_status} не найдено!'

    dinosaurs.update_one({'_id': dino_id}, {'$set': {'status': new_status}})