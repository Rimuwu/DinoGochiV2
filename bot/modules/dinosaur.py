from pprint import pprint
from random import choice, randint, choices
from time import time

from bot.config import mongo_client
from bot.const import DINOS, GAME_SETTINGS
from bot.modules.localization import log
from bot.modules.images import create_egg_image

dinosaurs = mongo_client.bot.dinosaurs
incubations = mongo_client.tasks.incubation

class Dino:

    def __init__(self, baseid):
        """Создание объекта динозавра."""
        self._id = baseid

        self.dino_id = 0
        self.owner_id = 0

        self.status = 'pass'
        self.name = 'name'
        self.quality = None

        self.stats = {
                'hp': 10, 'eat': 10,
                'game': 10, 'mood': 10,
                'energy': 10
        }

        self.activ_items = {
                'game': None, 'hunt': None,
                'journey': None, 'sleep': None,
                
                'armor': None,  'weapon': None,
                'backpack': None
        }

        self.UpdateData(dinosaurs.find_one({"_id": self._id}))

    def UpdateData(self, data):
        if data:
            self.__dict__ = data
        
    def __str__(self) -> str:
        return str(self)


    def view(self) :
        """Отображает все данные объекта."""

        print('DATA: ', end='')
        pprint(self.data)

    def update(self, update_data: dict):
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        self.data = dinosaurs.update_one({"_id": self._id}, update_data)
    
    def delete(self):
        dinosaurs.delete_one({'dino_id': self._id})
    
    def image(self, lang: str):
        """Сгенерировать изображение объекта
        """
        ...


class Egg:

    def __init__(self, baseid):
        """Создание объекта яйца."""
        
        self._id = baseid
        self.incubation_time = 0
        self.egg_id = 0
        self.owner_id = 0
        self.rarity = 'random'
        self.egg_id = 0

        self.UpdateData(incubations.find_one({"_id": self._id}))

    def UpdateData(self, data):
        if data:
            self.__dict__ = data

    def __str__(self) -> str:
        return str(self)


    def view(self):
        """ Отображает все данные объекта."""

        print('DATA: ', end='')
        pprint(self.data)

    def update(self, update_data: dict):
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        self.data = incubations.update_one({"_id": self._id}, update_data)
    
    def delete(self):
        incubations.delete_one({'_id': self._id})

    def image(self, lang: str='en'):
        """Сгенерировать изображение объекта.
        """
        t_inc = self.incubation_time - int(time())
        return create_egg_image(egg_id=self.egg_id, rare=self.rarity, seconds=t_inc, lang=lang)


def random_dino(quality: str='random') -> int:
    """Рандомизация динозавра по редкости
    """
    if quality == 'random':
        rarities = list(GAME_SETTINGS['dino_rarity'].keys())
        weights = list(GAME_SETTINGS['dino_rarity'].values())

        quality = choices(rarities, weights)[0]
    
    dino_id = choice(DINOS[quality])
    return dino_id
    
def incubation_dino(egg_id: int, owner_id: int, inc_time: int=0, rarity: str='random', dino_id: int=0):
    """Создание инкубируемого динозавра
    """

    dino = {
        'incubation_time': inc_time, 
        'egg_id': egg_id,
        'owner_id': owner_id,
        'rarity': rarity,
        'dino_id': dino_id
    }
    
    if inc_time == 0: #Стандартное время инкцбации 
        dino['incubation_time'] = int(time()) + GAME_SETTINGS['first_dino_time_incub']
    
    log(prefix='InsertEgg', message=f'owner_id: {owner_id} data: {dino}', lvl=0)
    return incubations.insert_one(dino)

def insert_dino(owner_id: int, dino_id: int=0, quality: str='random'):
    """Создания динозавра в базе
    """
    if not dino_id: dino_id = random_dino(quality)
    dino_data = DINOS['elements'][str(dino_id)]

    dino = {
       'dino_id': dino_id,
       'owner_id': owner_id,

       'status': 'pass',
       'name': dino_data['name'],
       'quality': None,

       'stats': {
            'hp': 100, 'eat': randint(70, 100),
            'game': randint(30, 90), 'mood': randint(20, 100),
            'energy': randint(80, 100)
        },

       'activ_items': {
            'game': None, 'hunt': None,
            'journey': None, 'sleep': None,
            
            'armor': None,  'weapon': None,
            'backpack': None
       }
    }
    dino['quality'] = quality or dino_data['quality']

    log(prefix='InsertDino', message=f'owner_id: {owner_id} dino_id: {dino["dino_id"]} name: {dino["name"]} quality: {dino["quality"]}', lvl=0)
    return dinosaurs.insert_one(dino)