from bot.config import mongo_client
friends = mongo_client.connections.friends

def get_frineds(userid: int) -> dict:
    """ Получает друзей (id) и запросы к пользователю
    
        Return\n
        { 'friends': [],
          'requests': [] }
    """
    friends_dict = {
        'friends': [],
        'requests': []
        }
    alt = {'friendid': 'userid', 
           'userid': 'friendid'
           }

    for st in ['userid', 'friendid']:
        data_list = list(friends.find({st: userid, 'type': 'friends'}))
        
        for conn_data in data_list:
            friends_dict['friends'].append(conn_data[alt[st]])

        if st == 'friendid':
            data_list = list(friends.find({st: userid, 'type': 'request'}))

            for conn_data in data_list:
                friends_dict['requests'].append(conn_data[alt[st]])
    return friends_dict

def insert_friend_connect(userid: int, friendid: int, action: str):
    """ Создаёт связь между пользователями
        friends, request
    """
    assert action in ['friends', 'request'], f'Неподходящий аргумент {action}'
    
    res = friends.find_one({
        'userid': userid,
        'friendid': friendid,
        'type': action
    })

    res2 = friends.find_one({
        'userid': friendid,
        'friendid': userid,
        'type': action
    })

    if not res and not res2:
        data = {
            'userid': userid,
            'friendid': friendid,
            'type': action
        }
        return friends.insert_one(data)
    return False