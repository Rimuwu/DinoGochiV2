from pprint import pprint
from random import randint, choice
from time import time

from bot import config
from bot.const import GAME_SETTINGS

dinosaurs = config.mongo_client.bot.dinosaurs

class Dino:

    def __init__(self, baseid = None) -> None:
        """Создание объекта динозавра."""
        
        # Берём из базы
        if baseid is not None:
            self.id = baseid
            self.data = dinosaurs.find_one({"_id": self.id})

            if self.data != None:
                if 'name' in self.data.keys():
                    self.name = self.data['name']
                else:
                    self.name = 'DinoEgg'
    
    def __str__(self) -> str:
        return f"DinoObj {self.name}"


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
    
def insert_dino(egg_id: int, owner_id: int, inc_time: int = 0, rarity: str = '', dino_id: int = 0):
    """Создания динозавра в базе на стадии инкубации
    """
    dino = {
        'status': 'incubation', 
        'incubation_time': inc_time, 
        'egg_id': egg_id,
        'owner_id': owner_id
        }
    
    if inc_time == 0: #Стандартное время инкцбации 
        dino['incubation_time'] = time() + GAME_SETTINGS['first_dino_time_incub']
    
    return dinosaurs.insert_one(dino)

def random_dino(baseid, quality: str = 'random', dino_id: int = 0):

        if quality == 'random':
            r_event = randint(1, 100)

            if r_event >= 1 and r_event <= 50:  # 50%
                quality = 'com'
            elif r_event > 50 and r_event <= 75:  # 25%
                quality = 'unc'
            elif r_event > 75 and r_event <= 90:  # 15%
                quality = 'rar'
            elif r_event > 90 and r_event <= 99:  # 9%
                quality = 'myt'
            elif r_event > 99 and r_event <= 100:  # 1%
                quality = 'leg'

        while dino_id == 0:
            p_var = choice(json_f['data']['dino'])
            dino = json_f['elements'][str(p_var)]
            if dino['image'][5:8] == quality:
                dino_id = p_var

        dino = json_f['elements'][str(dino_id)]
        del user['dinos'][str(dino_id_remove)]
        user['dinos'][Functions.user_dino_pn(user)] = {
            'dino_id': dino_id, "status": 'dino',
            'activ_status': 'pass_active', 'name': dino['name'],
            'stats': {"heal": 100, 
                      "eat": random.randint(70, 100), 
                      'game': random.randint(50, 100),
                      'mood': random.randint(7, 100), "unv": 100},
            'games': [],
            'quality': quality, 'dungeon': {"equipment": {'armor': None, 'weapon': None}}
        }

        users.update_one({"userid": user['userid']}, {"$set": {'dinos': user['dinos']}})