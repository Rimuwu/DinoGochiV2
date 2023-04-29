from random import choice, randint
from time import time

from bson.objectid import ObjectId

from bot.config import mongo_client
from bot.const import DINOS, GAME_SETTINGS
from bot.modules.data_format import random_code, random_quality
from bot.modules.images import create_dino_image, create_egg_image
from bot.modules.localization import log
from bot.modules.notifications import dino_notification

dinosaurs = mongo_client.bot.dinosaurs
incubations = mongo_client.tasks.incubation
dino_owners = mongo_client.connections.dino_owners

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

        self.status = 'pass' # game, journey, sleep, collecting, dungeon
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

        self.memory = {
            'games': [],
            'eat': []
        }

        find_result = dinosaurs.find_one({"_id": self._id})
        if not find_result:
            find_result = dinosaurs.find_one({"alt_id": self._id})
        if find_result:
            self.UpdateData(find_result)
        else:
            log('Динозавр не найден', 3)

    def UpdateData(self, data):
        if data:
            self.__dict__ = data
        
    def __str__(self) -> str:
        return self.name

    def update(self, update_data: dict):
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        data = dinosaurs.update_one({"_id": self._id}, update_data)
        # self.UpdateData(data) #Не получается конвертировать в словарь возвращаемый объект
    
    def delete(self):
        """ Удаление всего, что связано с дино
        """
        dinosaurs.delete_one({'dino_id': self._id})
        for collection in [game_task, sleep_task, journey_task, 
                           collecting_task]:
            collection.delete_many({'dino_id': self._id})


    def image(self, profile_view: int=1):
        """Сгенерировать изображение объекта
        """
        return create_dino_image(self.data_id, self.stats, self.quality, profile_view)

    def collecting(self, coll_type: str):
        return start_collecting(self._id, coll_type)
    
    def game(self, duration: int=1800, percent: int=1):
        return start_game(self._id, duration, percent)
    
    def journey(self, duration: int=1800):
        return start_journey(self._id, duration)
    
    def sleep(self, s_type: str='long', duration: int=1):
        return start_sleep(self._id, s_type, duration)
    
    @property
    def data(self):
        return get_dino_data(self.data_id)


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

    dino = {
        'incubation_time': inc_time + int(time()), 
        'egg_id': egg_id,
        'owner_id': owner_id,
        'quality': quality,
        'dino_id': dino_id
    }
    
    if inc_time == 0: #Стандартное время инкцбации 
        dino['incubation_time'] = int(time()) + GAME_SETTINGS['first_dino_time_incub']
    
    log(prefix='InsertEgg', message=f'owner_id: {owner_id} data: {dino}', lvl=0)
    return incubations.insert_one(dino)

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
    if quality in ['random', 'rar']: quality = random_quality()
    if not dino_id: dino_id = random_dino(quality)

    dino_data = get_dino_data(dino_id)
    dino = {
       'data_id': dino_id,
       'alt_id': f'{owner_id}_{random_code(8)}',

       'status': 'pass',
       'name': dino_data['name'],
       'quality': None,

       'notifications': {},

       'stats': {
            'heal': 100, 'eat': randint(70, 100),
            'game': randint(30, 90), 'mood': randint(20, 100),
            'energy': randint(80, 100)
        },

       'activ_items': {
            'game': None, 'collecting': None,
            'journey': None, 'sleep': None,
            
            'armor': None,  'weapon': None,
            'backpack': None
       },

       "memory": {
            'games': [],
            'eat': []
        },
    }

    dino['quality'] = quality or dino_data['quality']

    log(prefix='InsertDino', 
        message=f'owner_id: {owner_id} dino_id: {dino_id} name: {dino["name"]} quality: {dino["quality"]}', 
        lvl=0)

    result = dinosaurs.insert_one(dino)
    if owner_id != 0:
        # Создание связи, если передан id владельца
        create_dino_connection(result.inserted_id, owner_id)

    return result, dino['alt_id']

def start_game(dino_baseid: ObjectId, duration: int=1800, 
               percent: int=1):
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

async def end_sleep(dino_id: ObjectId, sleeperid: ObjectId, 
                    sec_time: int=0, send_notif: bool=True):
    """Заканчивает сон и отсылает уведомление.
       sec_time - время в секундах, сколько спал дино.
    """
    sleep_task.delete_one({'_id': sleeperid})

    dinosaurs.update_one({'_id': dino_id}, 
                         {'$set': {'status': 'pass'}})
    if send_notif:
        await dino_notification(dino_id, 'sleep_end', 
                            add_time_end=True,
                            secs=sec_time)

def start_journey(dino_baseid: ObjectId, duration: int=1800):
    """Запуск активности "путешествие". 
       + Изменение статуса динозавра 
    """

    game = {
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

def start_collecting(dino_baseid: ObjectId, coll_type: str):
    """Запуск активности "сбор пищи". 
       + Изменение статуса динозавра 
    """

    assert coll_type in ['collecting', 'hunt', 'fishing', 'all'], f'Неподходящий аргумент {coll_type}'

    game = {
        'dino_id': dino_baseid,
        'collecting_type': coll_type
    }
    result = collecting_task.insert_one(game)
    dinosaurs.update_one({"_id": dino_baseid}, 
                         {'$set': {'status': 'collecting'}})
    return result

def edited_stats(before: int, unit: int):
    """ Лёгкая функция проверки на 
        0 <= unit <= 100 
    """
    after = 0
    if before + unit > 100: after = 100
    elif before + unit < 0: after = 0
    else: after = before + unit

    return after