from bson.objectid import ObjectId

def add_mood(dino: ObjectId, key: str, unit: int, time: int):
    """ Добавляет в лог dino событие по key, которое влияет на настроение в размере unit в течении time секунд
    """
    print(dino, key, unit, time)
    
def mood_while_if(dino: ObjectId, key: str, characteristic: str, 
                  min_unit: int, max_unit: int, action: str = 'delete'):
    """ Добавляет в лог dino событие по key, которое влияет на настроение в пока его characteristic не меньше min_unit и не выше max_unit, 
    иначе acttion - delete / wait_event_end
    """
    print(dino, key, characteristic, min_unit, max_unit)