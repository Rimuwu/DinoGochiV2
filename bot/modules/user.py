import time

from bot import config
from bot.modules.dinosaur import Dino
from bot.modules.item import CreateItem
from bot.modules.localization import get_all_locales

users = config.mongo_client.bot.users


class User:

    def __init__(self, userid: int) -> None:
        """Создание объекта пользователя
           telegram = True - надо ли запрашивать данные из телеги.
        """
        self.id = userid
        self.data = users.find_one({"userid": self.id})
    
    def get_dinos(self) -> list:
        """Возвращает список с объектами динозавров."""
        dinosaurs = config.mongo_client.bot.dinosaurs
        dino_list = []

        for dino_obj in dinosaurs.find({'owner_id': self.id}):
            dino_list.append(Dino(dino_obj))

        return dino_list
    
    # def generate_inventory(self) -> list:
    #     inv = []
    #     for item_dict in self.data['inventory']:
    #         inv.append(CreateItem(item_data=item_dict).new())
        
    #     return inv
    
    def view(self) -> None:
        """ Отображает все данные объекта."""

        print(f'ID: {self.id}')
        print(f'DATA: {self.data}')
        print(f'dino_len: {len(self.dinos)}')
    
    def update(self, update_data) -> None:
        """
        {"$set": {'coins': 12}} - установить
        {"$inc": {'coins': 12}} - добавить
        """
        self.data = users.update_one({"userid": self.id}, update_data)


def insert_user(userid:int, lang_code:str) -> None:
    loc_codes = get_all_locales('language_code')

    if lang_code not in loc_codes.keys():
        lang_code = 'en'

    user_dict = {
        'userid': userid,
        'last_message': int(time.time()),
        'last_markup': 'main_menu',
        'notifications': {},
        'settings': {'notifications': {},
                    'dino_id': None,
                    'profile_view': 1,
                    'inv_view': [2, 3],
                    'language_code': lang_code,
                    },
        'coins': 10, 'lvl': 0, 'xp': 0,
        'dead_dinos': 0,
        'user_dungeon': { 'equipment': {'backpack': None},
                          'statistics': []
                        } 
    }

    users.insert_one(user_dict)