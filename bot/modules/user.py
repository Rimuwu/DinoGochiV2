from random import choice
from time import time

from telebot.types import User as teleUser

from bot.config import mongo_client
from bot.const import GAME_SETTINGS as GS
from bot.exec import bot
from bot.modules.data_format import escape_markdown, seconds_to_str, user_name
from bot.modules.dinosaur import Dino, Egg
from bot.modules.friends import get_frineds
from bot.modules.item import AddItemToUser
from bot.modules.item import get_data as get_item_data
from bot.modules.item import get_name
from bot.modules.localization import get_data, t
from bot.modules.logs import log
from bot.modules.notifications import user_notification
from bot.modules.referals import get_code_owner, get_user_sub

users = mongo_client.bot.users
items = mongo_client.bot.items
dinosaurs = mongo_client.bot.dinosaurs
products = mongo_client.bot.products
dead_dinos = mongo_client.bot.dead_dinos

incubations = mongo_client.tasks.incubation
dino_owners = mongo_client.connections.dino_owners
friends = mongo_client.connections.friends
subscriptions = mongo_client.tasks.subscriptions
referals = mongo_client.connections.referals

class User:

    def __init__(self, userid: int):
        """Создание объекта пользователя
        """
        self.userid = userid

        self.last_message_time = 0
        self.last_markup = 'main_menu'

        self.settings = {
            'notifications': True,
            'last_dino': None, #храним ObjectId
            'profile_view': 1,
            'inv_view': [2, 3],
            'my_name': '' # Как вас называет динозавр
            }
            
        self.coins = 100
        self.lvl = 0
        self.xp = 0

        self.dungeon = { 
            'quest_ended': 0,
            'dungeon_ended': 0
        }
        
        self.UpdateData(users.find_one({"userid": self.userid})) #Обновление данных
        
    def UpdateData(self, data):
        if data: self.__dict__ = data
    
    def get_dinos(self, all_dinos: bool=True) -> list:
        """Возвращает список с объектами динозавров.
           all_dinos - Если False то не запросит совместных динозавров 
        """
        dino_list = get_dinos(self.userid, all_dinos)
        self.dinos = dino_list
        return dino_list

    @property
    def get_col_dinos(self) -> int:
        col = col_dinos(self.userid)
        self.col_dinos = col
        return col
    
    @property
    def get_eggs(self) -> list:
        """Возвращает список с объектами динозавров."""
        eggs_list = get_eggs(self.userid)
        self.eggs = eggs_list
        return eggs_list
    
    @property
    def get_inventory(self):
        """Возвращает список с предметами в инвентаре"""
        inv, count = get_inventory(self.userid)
        self.inventory = inv
        return inv, count

    @property
    def get_friends(self) -> dict:
        """Возвращает словарь с 2 видами связей
           friends - уже друзья
           requests - запрос на добавление
        """
        friends_dict = get_frineds(self.userid)
        self.friends = friends_dict
        return friends_dict

    @property
    def premium(self) -> bool: return premium(self.userid)

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

        for collection in [items, products, dead_dinos, incubations, referals]:
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
            
            #Удаляем его связь
            dino_owners.delete_one({'_id': conn['_id']})
        
        # Удаление связи с друзьями
        friends_conn = list(friends.find({'userid': self.userid}))
        friends_conn2 = list(friends.find({'friendid': self.userid}))
        
        for conn in [friends_conn, friends_conn2]:
            for obj in conn: friends.delete_one({'_id': obj['_id']})

        # Удаляем юзера
        self.delete()
    
    def delete(self):
        """Удаление юзера из базы.
        """
        users.delete_one({'userid': self.userid})
    
    def get_last_dino(self):
        """Возвращает последнего динозавра или None
        """
        return last_dino(self)
    
    def max_dino_col(self):
        """Возвращает доступное количесвто динозавров, беря во внимание уровень и статус,
           считает сколько динозавров у юзера вместе с лимитом
           {
             'standart': { 'now': 0, 'limit': 0},
             'additional': {'now': 0, 'limit': 1}
            }
        """
        return max_dino_col(self.lvl, self.userid, self.premium)


def insert_user(userid: int):
    """Создание пользователя"""
    log(prefix='InsertUser', message=f'User: {userid}', lvl=0)
    return users.insert_one(User(userid).__dict__)

def get_dinos(userid: int, all_dinos: bool = True) -> list:
    """Возвращает список с объектами динозавров."""
    dino_list = []

    if all_dinos:
        res = list(dino_owners.find({'owner_id': userid}, 
                                          {'dino_id': 1}))
    else:
        res = list(dino_owners.find({'owner_id': userid, 'type': 'owner'}, {'dino_id': 1}))

    for dino_obj in res:
        dino_list.append(Dino(dino_obj['dino_id']))

    return dino_list

def get_dinos_and_owners(userid: int) -> list:
    """Возвращает список с объектами динозавров и их владельцами, а так же правами на динозавра"""
    data = []
    for dino_obj in dino_owners.find({'owner_id': userid}):
        data.append({'dino': Dino(dino_obj['dino_id']), 'owner_type': dino_obj['type']})

    return data

def col_dinos(userid: int) -> int:
    return len(list(dino_owners.find({'owner_id': userid}, {'_id': 1})))
    
def get_eggs(userid: int) -> list:
    """Возвращает список с объектами динозавров."""
    eggs_list = []
    for egg in incubations.find({'owner_id': userid}):
        eggs_list.append(Egg(egg['_id']))

    return eggs_list

def get_inventory(userid: int):
    inv, count = [], 0

    for item_dict in items.find({'owner_id': userid}, 
                                {'_id': 0, 'owner_id': 0}):
        item = {
            'item': item_dict['items_data'], 
            "count": item_dict['count']
            }
        inv.append(item)
        count += item_dict['count']

    return inv, count

def items_count(userid: int):
    return len(list(items.find({'owner_id': userid}, {'_id': 1})))

def last_dino(user: User):
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

def award_premium(userid:int, end_time):
    """
    Присуждение премиум статуса юзеру
    {
        'userid': int,
        'sub_start': int,
        'sub_end': int | str (inf),
        'end_notif': bool (отправлено ли уведомление о окончании подписки)
    }
    """
    user_doc = subscriptions.find_one({'userid': userid})
    if user_doc:
        if type(end_time) == str:
            user_doc['sub_end'] = end_time
        elif type(end_time) == int:
            user_doc['sub_end'] += end_time
        
        subscriptions.update_one({'userid': userid}, {'$set': {'sub_end': user_doc['sub_end']}})
    else:
        if type(end_time) == int:
            end_time = int(time()) + end_time #type: ignore

        user_doc = {
            'userid': userid,
            'sub_start': int(time()),
            'sub_end': end_time,
            'end_notif': False
        }
        subscriptions.insert_one(user_doc)

def max_dino_col(lvl: int, user_id: int=0, premium: bool=False):
    """Возвращает доступное количесвто динозавров, беря во внимание уровень и статус
       Если передаётся user_id то считает сколько динозавров у юзера вместе с лимитом
       {
          'standart': { 'now': 0, 'limit': 0},
          'additional': {'now': 0, 'limit': 1}
        }
    """
    col = {
        'standart': {
            'now': 0, 'limit': 0
        },
        'additional': {
            'now': 0, 'limit': 1
        }
    }

    if premium: col['standart']['limit'] += 1
    col['standart']['limit'] += (lvl // 20 + 1) - lvl // 80

    if user_id:
        dinos = dino_owners.find({'owner_id': user_id})
        for dino in dinos:
            if dino['type'] == 'owner': col['standart']['now'] += 1
            else: col['additional']['now'] += 1

    return col

def max_lvl_xp(lvl: int): return 5 * lvl * lvl + 50 * lvl + 100

async def experience_enhancement(userid: int, xp: int):
    """Повышает количество опыта, если выполнены условия то повышает уровень и отпарвляет уведомление
    """
    user = users.find_one({'userid': userid})
    if user:
        lvl = 0
        xp = user['xp'] + xp

        try:
            chat_user = await bot.get_chat_member(userid, userid)
            lang = chat_user.user.language_code
            name = user_name(chat_user.user)
        except: 
            lang = 'en'
            name = 'name'

        lvl_messages = get_data('notifications.lvl_up', lang)

        while xp > 0:
            max_xp = max_lvl_xp(user['lvl'])
            if max_xp <= xp:
                xp -= max_xp
                lvl += 1
                if lvl >= 100: break

                if str(user['lvl'] + lvl) in lvl_messages: 
                    add_way = str(user['lvl'] + lvl)
                else: add_way = 'standart'

                await user_notification(userid, 'lvl_up', lang, 
                                        user_name=name,
                                        lvl=user['lvl'] + lvl, 
                                        add_way=add_way)
            else: break

        if lvl: users.update_one({'userid': userid}, {'$inc': {'lvl': lvl}})
        users.update_one({'userid': userid}, {'$set': {'xp': xp}})

        # Выдача награда за реферал
        if user['lvl'] < 5 and user['lvl'] + lvl >= GS['referal']['award_lvl']:
            sub = get_user_sub(userid)
            if sub:
                code = sub['code']
                referal = get_code_owner(code)
                if referal:
                    code_owner = referal['userid']
                    random_item = choice(GS['referal']['award_items'])
                    item_name = get_name(random_item, lang)

                    AddItemToUser(userid, random_item)
                    await user_notification(code_owner, 'referal_award', lang, 
                                        user_name=name,
                                        lvl=user['lvl'] + lvl, item_name=item_name)

def user_info(data_user: teleUser, lang: str, secret: bool = False):
    user = User(data_user.id)
    return_text = ''
    
    premium = t('user_profile.no_premium', lang)
    if user.premium:
        find = subscriptions.find_one({'userid': data_user.id})
        if find:
            if find['sub_end'] == 'inf':
                premium = '♾'
            else:
                premium = seconds_to_str(
                    find['sub_end'] - find['sub_start'], lang)

    friends = get_frineds(data_user.id)
    friends_count = len(friends['friends'])
    request_count = len(friends['requests'])
    
    dinos = get_dinos_and_owners(data_user.id)
    eggs = get_eggs(data_user.id)
    
    m_name = escape_markdown(user_name(data_user))

    return_text += t('user_profile.user', lang,
                     name = m_name,
                     userid = data_user.id,
                     premium_status = premium
                     )
    return_text += '\n\n'
    return_text += t('user_profile.level', lang,
                     lvl=user.lvl, xp_now=user.xp,
                     max_xp=max_lvl_xp(user.lvl),
                     coins=user.coins
                     )
    return_text += '\n\n'
    if not secret:
        dd = dead_dinos.find({'owner_id': user.userid})
        return_text += t(f'user_profile.dinosaurs', lang,
                        dead=len(list(dd)), dino_col = len(dinos)
                        )
        return_text += '\n\n'
        for iter_data in dinos:
            dino = iter_data['dino']
            dino_status = t(f'user_profile.stats.{dino.status}', lang)
            dino_rare_dict = get_data(f'rare.{dino.quality}', lang)
            dino_rare = f'{dino_rare_dict[2]} {dino_rare_dict[1]}'
            
            if iter_data['owner_type'] == 'owner': 
                dino_owner = t(f'user_profile.dino_owner.owner', lang)
            else:
                dino_owner = t(f'user_profile.dino_owner.noowner', lang)
            
            return_text += t('user_profile.dino', lang,
                            dino_name=escape_markdown(dino.name), 
                            dino_status=dino_status,
                            dino_rare=dino_rare,
                            owner=dino_owner,
                            age=seconds_to_str(dino.age.days * 86400, lang, True)
                        )
        
        for egg in eggs:
            egg_rare_dict = get_data(f'rare.{egg.quality}', lang)
            egg_rare = f'{egg_rare_dict[3]}'
            return_text += t('user_profile.egg', lang,
                            egg_quality=egg_rare, 
                            remained=
                            seconds_to_str(egg.incubation_time - int(time()), lang, True)
                        )

    return_text += t('user_profile.friends', lang,
                     friends_col=friends_count,
                     requests_col=request_count
                     )
    
    if not secret:
        items, count = user.get_inventory
        
        return_text += '\n\n'
        return_text += t('user_profile.inventory', lang,
                        items_col=count
                        )

    return return_text

def premium(userid: int):
    res = subscriptions.find_one({'userid': userid})
    return bool(res)

def take_coins(userid: int, col: int, update: bool = False) -> bool:
    """Функция проверяет, можно ли отнять / добавить col монет у / к пользователя[ю]
       Если updatе - то обновляет данные
    """
    user = users.find_one({'userid': userid})
    if user:
        coins = user['coins']
        if coins + col < 0: return False
        else: 
            if update:
                users.update_one({'userid': userid}, 
                                 {'$inc': {'coins': col}})
            return True
    return False

def get_dead_dinos(userid: int):
    return list(dead_dinos.find({'owner_id': userid}))

def count_inventory_items(userid: int, find_type: list):
    """ Считает сколько предметов нужных типов в инвентаре
    """
    result = 0
    for item in items.find({'owner_id': userid}, 
                                {'_id': 0, 'owner_id': 0}):
        item_data = get_item_data(item['items_data']['item_id'])
        item_type = item_data['type']

        if item_type in find_type or not find_type: result += 1
    return result

async def user_in_chat(userid: int, chatid: int):
    statuss = ['creator', 'administrator', 'member']
    try:
        result = await bot.get_chat_member(chat_id=chatid, user_id=userid)
    except Exception as e: return False

    if result.status in statuss: return True
    return False