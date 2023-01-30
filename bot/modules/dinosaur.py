from pprint import pprint
from random import randint, choice
from time import time

from bot import config
from bot.const import GAME_SETTINGS, DINOS
from bot.modules.data_format import random_quality

dinosaurs = config.mongo_client.bot.dinosaurs
incubations = config.mongo_client.bot.incubation

class Dino:

    def __init__(self, baseid = None) -> None:
        """Создание объекта динозавра."""
        
        self.id = baseid
        self.data = dinosaurs.find_one({"_id": self.id})
    
    def __str__(self) -> str:
        return f"Dino {self.data['name']}"


    def view(self) -> None:
        """ Отображает все данные объекта."""

        print('DATA: ', end='')
        pprint(self.data)

    def update(self, update_data: dict[str, int]) -> None:
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        self.data = dinosaurs.update_one({"_id": self.id}, update_data)
    
def incubation_dino(egg_id: int, owner_id: int, inc_time: int = 0, rarity: str = '', dino_id: int = 0):
    """Создание инкубируемого динозавра
    """

    dino = {
        'incubation_time': inc_time, 
        'egg_id': egg_id,
        'owner_id': owner_id,
        'rarity': 'random',
        'dino_id': 0
    }
    
    if inc_time == 0: #Стандартное время инкцбации 
        dino['incubation_time'] = time() + GAME_SETTINGS['first_dino_time_incub']
    
    if rarity: dino['rarity'] = rarity
    if dino_id: dino['dino_id'] = dino_id
    
    return incubations.insert_one(dino)

def insert_dino(owner_id: int, dino_id: int, quality: str=''):
    """Создания динозавра в базе
    """

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
            'sleep': 100
        },

       'activ_items': {
            'game': None, 'hunt': None,
            'journey': None, 'sleep': None,
            'armor': None,  'weapon': None,
            'backpack': None
       }
    }

    dino['quality'] = quality or dino_data['quality']

    return dinosaurs.insert_one(dino)

def random_dino(quality: str='random'):
    """ Рандомизация динозавра по редкости
    """

    if quality == 'random':
        quality = random_quality()

    return choice(DINOS[quality])

