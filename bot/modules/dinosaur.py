from pprint import pprint
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
    
def insert_dino(egg_id: int, owner_id: int):
    dino = {
        'status': 'incubation', 
        'incubation_time': time() + GAME_SETTINGS['first_dino_time_incub'], 
        'egg_id': egg_id,
        'owner_id': owner_id
        }
    
    return dinosaurs.insert_one(dino)