import time

from bot.config import mongo_client
from bot.modules.dinosaur import Dino
from bot.modules.item import CreateItem
from bot.modules.localization import available_locales

users = mongo_client.bot.users
items = mongo_client.bot.items
dinosaurs = mongo_client.bot.dinosaurs


class User:

    def __init__(self, userid: int) -> None:
        """Создание объекта пользователя
        """
        self.userid = int(userid),

        self.last_message = 0,
        self.last_markup = 'main_menu',

        self.notifications = {}
        self.settings = {
            'notifications': {},
            'dino_id': None,
            'profile_view': 1,
            'inv_view': [2, 3],
            'language_code': 'en',
            },
            
        self.coins = 10, 
        self.lvl = 0, 
        self.xp = 0,
        self.dead_dinos = 0,

        self.user_dungeon = { 
            'equipment': {'backpack': None},
            'statistics': []
            }
        
        self.FromBase() #Импортируем данные из базы
        
    def FromBase(self):
        userdata = users.find_one({"userid": self.userid})

        if userdata:
            self.__dict__ = userdata
    
    def get_dinos(self) -> list:
        """Возвращает список с объектами динозавров."""
        dino_list = []

        for dino_obj in dinosaurs.find({'owner_id': self.userid}, {'_id': 1}):
            dino_list.append(Dino(dino_obj['_id']))

        self.dinos = dino_list
        return dino_list
    
    def get_inventory(self) -> list:
        inv = []

        for item_dict in items.find({'owner_id': self.userid}, {'_id': 0, 'owner_id': 0}):
            item = {
                'item': CreateItem(item_data=item_dict['items_data']).new(), 
                "count": item_dict['count']
                }
            inv.append(item)
        
        self.inventory = inv
        return inv
    
    def view(self) -> None:
        """ Отображает все данные объекта."""

        print(f'userid: {self.userid}')
        print(f'DATA: {self.__dict__}')
    
    def update(self, update_data) -> None:
        """
        {"$set": {'coins': 12}} - установить
        {"$inc": {'coins': 12}} - добавить
        """
        self.data = users.update_one({"userid": self.userid}, update_data)


def insert_user(userid: int, lang_code: str):

    if lang_code not in available_locales:
        lang_code = 'en'

    user_dict = {
        'userid': userid,
        'last_message': int(time.time()),
        'last_markup': 'main_menu',
        'notifications': {},
        'settings': { 'notifications': {},
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

    return users.insert_one(user_dict)