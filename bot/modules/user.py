import time

from bot.config import mongo_client
from bot.modules.dinosaur import Dino, Egg
from bot.modules.localization import log

users = mongo_client.bot.users
items = mongo_client.bot.items
dinosaurs = mongo_client.bot.dinosaurs

incubations = mongo_client.tasks.incubation
dino_owners = mongo_client.connections.dino_owners
friends = mongo_client.connections.friends


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
            'last_dino': None, #храним ObjectId
            'profile_view': 1,
            'inv_view': [2, 3],
            'faq': True,
            'premium_status': 0
            }
            
        self.coins = 10
        self.lvl = 0
        self.xp = 0
        self.dead_dinos = 0

        self.user_dungeon = { 
            'statistics': [],
            'quests': {
                'activ_quests': [],
                'max_quests': 5,
                'ended': 0
                }
            }
        
        self.UpdateData(users.find_one({"userid": self.userid})) #Обновление данных
        
    def UpdateData(self, data):
        if data:
            self.__dict__ = data
    
    def get_dinos(self) -> list[Dino]:
        """Возвращает список с объектами динозавров."""
        dino_list = get_dinos(self.userid)
        self.dinos = dino_list
        return dino_list

    def get_col_dinos(self) -> int:
        col = col_dinos(self.userid)
        self.col_dinos = col
        return col
    
    def get_eggs(self) -> list[Egg]:
        """Возвращает список с объектами динозавров."""
        eggs_list = get_eggs(self.userid)
        self.eggs = eggs_list
        return eggs_list
    
    def get_inventory(self) -> list[dict]:
        """Возвращает список с предметами в инвентаре"""
        inv = get_inventory(self.userid)
        self.inventory = inv
        return inv

    def get_friends(self) -> dict[str, list[int]]:
        """Возвращает словарь с 2 видами связей
           friends - уже друзья
           requests - запрос на добавление
        """
        friends_dict = get_frineds(self.userid)
        self.friends = friends_dict
        return friends_dict
    
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

        for collection in [items]:
            collection.delete_many({'owner_id': self.userid})

        """ При полном удалении есть возможность, что у динозавра
            есть другие владельцы, значит мы должны передать им полные права
            или наобраот удалить, чтобы не остался пустой динозавр
        """
        #запрашиваем все связи с владельцем
        dinos_conn = list(dino_owners.find({'owner_id': self.userid}))
        for conn in dinos_conn:
            #Если он главный
            if conn['type'] == 'owner':
                #Удаляем его связь
                dino_owners.delete_one({'_id': conn['_id']})

                #Запрашиваем всех владельцев динозавра (тут уже не будет главного)
                alt_conn_fo_dino = list(dino_owners.find(
                    {'dino_id': conn['dino_id'], 'type': 'add_owner'}))

                #Проверяем, пустой ли список
                if len(alt_conn_fo_dino) > 1:
                    #Связь с кем то есть, ищем первого попавшегося и делаем главным
                    dino_owners.update_one({'dino_id': conn['dino_id']}, {'$set': {'type': 'owner'}})
                else:
                    # Если пустой, то удаляем динозавра (связи уже нет)
                    Dino(conn['dino_id']).delete()

        # Удаляем юзера
        self.delete()
    
    def delete(self):
        """Удаление юзера из базы.
        """
        users.delete_one({'userid': self.userid})
    
    def get_last_dino(self) -> Dino | None:
        """Возвращает последнего динозавра или None
        """
        return last_dino(self)


def insert_user(userid: int):
    user_dict = {
        'userid': userid,

        'last_message_time': int(time.time()),
        'last_markup': 'main_menu',

        'settings': { 'notifications': True,
                      'last_dino': None,
                      'profile_view': 1,
                      'inv_view': [2, 3], 
                      'faq': True
                    },
        'coins': 10, 'lvl': 0, 'xp': 0,
        'dead_dinos': 0,

        'user_dungeon': { 
            'statistics': [],
            'quests': {
                'activ_quests': [],
                'max_quests': 5,
                'ended': 0
                }
            }
    }

    log(prefix='InsertUser', message=f'User: {userid}', lvl=0)
    return users.insert_one(user_dict)

def get_dinos(userid) -> list[Dino]:
    """Возвращает список с объектами динозавров."""
    dino_list = []
    for dino_obj in dino_owners.find({'owner_id': userid}, {'dino_id': 1}):
        dino_list.append(Dino(dino_obj['dino_id']))

    return dino_list

def col_dinos(userid) -> int:
    return len(list(dino_owners.find({'owner_id': userid}, {'_id': 1})))
    
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

def get_frineds(userid) -> dict[str, list[int]]:
    friends_dict = {
        'friends': [],
        'requests': []
        }
    alt = {'friendid': 'userid', 
           'userid': 'friendid'
           }

    for st in ['userid', 'friendid']:
        data_list = friends.find({st: userid, 'type': 'friends'})
        for conn_data in data_list:
            friends_dict['friends'].append(conn_data[alt[st]])

        if st == 'userid':
            data_list = friends.find({st: userid, 'type': 'requests'})
            for conn_data in data_list:
                friends_dict['requests'].append(conn_data[alt[st]])

    return friends_dict

def last_dino(user: User) -> Dino | None:
    """Возвращает последнего выбранного динозавра.
       Если None - вернёт первого
       Если нет динозавров - None
    """
    last_dino = user.settings['last_dino']
    if last_dino:
        dino = dinosaurs.find_one({'_id': last_dino}, {"_id": 1})
        if dino:
            return Dino(dino['_id'])
        else:
            user.update({'$set': {'settings.last_dino': None}})
            return last_dino(user)
    else:
        dino_lst = user.get_dinos()
        if len(dino_lst):
            dino = dino_lst[0]
            user.update({'$set': {'settings.last_dino': dino._id}})
            return dino
        else:
            user.update({'$set': {'settings.last_dino': None}})
            return None