from random import randint

from bson.objectid import ObjectId
from bot.modules.dinosaur import Dino, edited_stats, get_dino_data
from bot.modules.localization import t
from bot.modules.notifications import dino_notification
from bot.modules.item import get_data, get_name


async def downgrade_accessory(dino: Dino, acc_type: str):
    """Понижает прочность аксесуара
       Return
       >>> True - прочность понижена
       >>> False - неправильный предмет / нет предмета
    """
    item = dino.activ_items[acc_type]

    if item:
        if 'abilities' in item and 'endurance' in item['abilities']:
            num = randint(0, 2)
            item['abilities']['endurance'] -= num

            if item['abilities']['endurance'] <= 0:
                dino.update({"$set": {f'activ_items.{acc_type}': None}})
                await dino_notification(dino._id, 'acc_broke')
            else:
                dino.update({"$inc": {f'activ_items.{acc_type}': num}})
            return True
        else:
            return False
    else:
        return False

def check_accessory(dino: Dino, item_id: str, downgrade: bool=False):
    """Проверяет, активирован ли аксессуар с id - item_id
       downgrade - если активирован, то вызывает понижение прочности предмета
    """
    data_item = get_data(item_id) #Получаем данные из json
    acces_item = dino.activ_items[data_item['type'][:-3]] #предмет / None

    if acces_item:
        if acces_item['item_id'] == item_id:
            if downgrade:
                return downgrade_accessory(dino, data_item['type'])
            else:
                return True
        else:
            return False
    else:
        return False

def exchange_item(item: dict, from_user: int, to_user: int, 
                  count: int = 1):
    ...



def use_item(userid: int, lang: str, item: dict, count: int, 
             dino: Dino | None = None, combine_item: dict = {}):
    return_text = ''
    dino_update_list = []
    use_status, send_status, use_baff_status = True, True, True
    
    item_id: str = item['item_id']
    data_item: dict = get_data(item_id)
    item_name: str = get_name(item_id, lang)
    type_item: str = data_item['type']
    
    if type_item == 'eat' and dino:
        
        if dino.status == 'sleep':
            # Если динозавр спит, отменяем использование и говорим что он спит.
            return_text = t('item_use.status_sleep', lang)
            use_status = False
        
        else:
            # Если динозавр не спит, то действует в соответсвии с класом предмета.
            if data_item['class'] == 'ALL' or (
                data_item['class'] == dino.data['class']):
                # Получаем конечную характеристику
                eat_stat = edited_stats(dino.stats['eat'], 
                                   data_item['act'] * count)
                # Добавляем словарь в список обновлений, которые будут выполнены по окончанию работы
                dino_update_list.append({
                    '$set': {'stats.eat': eat_stat}
                    })

                return_text = t('item_use.eat.great', lang, 
                         item_name=item_name, eat_stat=eat_stat)
            
            else:
                # Если еда не соответствует классу, то убираем дполнительные бафы.
                use_baff_status = False
                loses_eat = randint(0, (data_item['act'] * count) // 2)
                loses_mood = randint(1, 10)
                # Получаем конечную характеристики
                eat_stat = edited_stats(dino.stats['eat'], loses_eat)
                mood_stat = edited_stats(dino.stats['mood'], loses_mood)
                # Добавляем словарь в список обновлений, которые будут выполнены по окончанию работы
                dino_update_list.append({
                    '$set': {'stats.eat': eat_stat,
                             "stats.mood": mood_stat
                            }
                    })
                
                return_text = t('item_use.eat.bad', lang, item_name=item_name,
                         loses_eat=loses_eat, loses_mood=loses_mood)
    
    elif type_item in ['game_ac', "journey_ac", "hunt_ac", "unv_ac", 'weapon', 'armor', 'backpack'] and dino:
        
        if dino.status == 'sleep':
            # Если динозавр спит, отменяем использование и говорим что он спит.
            return_text = t('item_use.status_sleep', lang)
            use_status = False
    
    
    print(use_status, send_status, use_baff_status)
    print(dino_update_list)
    print(return_text)
    return send_status, return_text