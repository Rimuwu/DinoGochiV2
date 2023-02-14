import time

from bot.config import mongo_client
from bot.modules.dinosaur import Dino, Egg
from bot.modules.localization import log

users = mongo_client.bot.users
items = mongo_client.bot.items
dinosaurs = mongo_client.bot.dinosaurs
incubations = mongo_client.tasks.incubation


class User:

    def __init__(self, userid: int):
        """Создание объекта пользователя
        """
        self.userid = userid

        self.last_message = 0
        self.last_markup = 'main_menu'

        self.notifications = {}
        self.settings = {
            'notifications': True,
            'dino_id': None,
            'profile_view': 1,
            'inv_view': [2, 3],
            'faq': True
            }
            
        self.coins = 10
        self.lvl = 0
        self.xp = 0
        self.dead_dinos = 0

        self.user_dungeon = { 'statistics': [] }
        
        self.UpdateData(users.find_one({"userid": self.userid})) #Обновление данных
        
    def UpdateData(self, data):
        if data:
            self.__dict__ = data
    
    def get_dinos(self) -> list:
        """Возвращает список с объектами динозавров."""
        dino_list = get_dinos(self.userid)
        self.dinos = dino_list
        return dino_list
    
    def get_eggs(self) -> list:
        """Возвращает список с объектами динозавров."""
        eggs_list = get_eggs(self.userid)
        self.eggs = eggs_list
        return eggs_list
    
    def get_inventory(self) -> list:
        inv = get_inventory(self.userid)
        self.inventory = inv
        return inv

    def get_friends(self) -> list:
        ...
    
    def view(self):
        """ Отображает все данные объекта."""

        print(f'userid: {self.userid}')
        print(f'DATA: {self.__dict__}')
    
    def update(self, update_data) -> None:
        """
        {"$set": {'coins': 12}} - установить
        {"$inc": {'coins': 12}} - добавить
        """
        data = users.update_one({"userid": self.userid}, update_data)
        # self.UpdateData(data) #Не получается конвертировать в словарь возвращаемый объект

    def full_delete(self):
        """Удаление юзера и всё с ним связанное из базы.
        """
        for collection in [items, dinosaurs]:
            collection.delete_many({'owner_id': self.userid})
        
        users.delete_one({'userid': self.userid})
    
    def delete(self):
        """Удаление юзера из базы.
        """
        users.delete_one({'userid': self.userid})


def insert_user(userid: int):

    user_dict = {
        'userid': userid,
        'last_message': int(time.time()),
        'last_markup': 'main_menu',
        'notifications': {},
        'settings': { 'notifications': True,
                      'dino_id': None,
                      'profile_view': 1,
                      'inv_view': [2, 3], 
                      'faq': True
                    },
        'coins': 10, 'lvl': 0, 'xp': 0,
        'dead_dinos': 0,
        'user_dungeon': { 'statistics': [] } 
    }

    log(prefix='InsertUser', message=f'User: {userid}', lvl=0)
    return users.insert_one(user_dict)

def get_dinos(userid) -> list:
    """Возвращает список с объектами динозавров."""
    dino_list = []
    for dino_obj in dinosaurs.find({'owner_id': userid}, {'_id': 1}):
        dino_list.append(Dino(dino_obj['_id']))

    return dino_list
    
def get_eggs(userid) -> list:
    """Возвращает список с объектами динозавров."""
    eggs_list = []
    for egg in incubations.find({'owner_id': userid}):
        eggs_list.append(Egg(egg['_id']))

    return eggs_list

def get_inventory(userid) -> list:
    inv = []
    for item_dict in items.find({'owner_id': userid}, {'_id': 0, 'owner_id': 0}):
        item = {
            'item': item_dict['items_data'], 
            "count": item_dict['count']
            }
        inv.append(item)
    return inv