from random import randint, shuffle

from bot.config import mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.dinosaur import Dino, edited_stats
from bot.modules.item import (AddItemToUser,
                              CalculateAbilitie, CheckItemFromUser,
                              DowngradeItem, EditItemFromUser,
                              RemoveItemFromUser, counts_items, get_data,
                              get_item_dict, get_name, item_code, is_standart)
from bot.modules.localization import t
from bot.modules.logs import log
from bot.modules.markup import confirm_markup, count_markup, markups_menu
from bot.modules.notifications import dino_notification
from bot.modules.states_tools import ChooseStepState
from bot.modules.user import experience_enhancement, User
from bot.modules.data_format import random_dict, list_to_inline
from bot.modules.images import create_eggs_image

users = mongo_client.bot.users
items = mongo_client.bot.items

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

async def end_craft(transmitted_data: dict):
    """ Завершает крафт удаляя и создавая предметы (не понижает прочность предметов и не удаляет сам рецепт)
    """
    materials = transmitted_data['materials']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    data_item = transmitted_data['data_item']
    count = transmitted_data['count']
    lang = transmitted_data['lang']
    
    # Удаление материалов
    for iteriable_item in materials['delete']:
        item_id = iteriable_item['item_id']
        RemoveItemFromUser(userid, item_id)

    # Добавление предметов
    for create_data in data_item['create']:
        if create_data['type'] == 'create':
            preabil = create_data.get('abilities', {}) # Берёт характеристики если они есть
            AddItemToUser(userid, create_data['item'], 1, preabil)
    
    # Вычисление опыта за крафт
    if 'rank' in data_item.keys():
        xp = GAME_SETTINGS['xp_craft'][data_item['rank']] * count
    else:
        xp = GAME_SETTINGS['xp_craft']['common'] * count

    # Начисление опыта за крафт
    await experience_enhancement(userid, xp)
    
    # Создание сообщения
    created_items = []
    for i in data_item['create']:
        created_items.append(i['item'])
    
    await bot.send_message(chatid, t('item_use.recipe.create', lang, 
                                     items=counts_items(created_items*count, lang)), 
                           parse_mode='Markdown', reply_markup=markups_menu(userid, 'last_menu', lang))

async def use_item(userid: int, chatid: int, lang: str, item: dict, count: int=1, 
             dino=None, combine_item: dict = {}):
    return_text = 'no_text'
    dino_update_list = []
    use_status, send_status, use_baff_status = True, True, True

    item_id: str = item['item_id']
    data_item: dict = get_data(item_id)
    item_name: str = get_name(item_id, lang)
    type_item: str = data_item['type']
    
    if type_item == 'eat' and dino:
        
        if dino.status == 'sleep':
            # Если динозавр спит, отменяем использование и говорим что он спит.
            return_text = t('item_use.eat.sleep', lang)
            use_status = False
        
        else:
            # Если динозавр не спит, то действует в соответсвии с класом предмета.
            if data_item['class'] == 'ALL' or (
                data_item['class'] == dino.data['class']):
                # Получаем конечную характеристику
                dino.stats['eat'] = edited_stats(dino.stats['eat'], 
                                   data_item['act'] * count)

                return_text = t('item_use.eat.great', lang, 
                         item_name=item_name, eat_stat=dino.stats['eat'])
            
            else:
                # Если еда не соответствует классу, то убираем дполнительные бафы.
                use_baff_status = False
                loses_eat = randint(0, (data_item['act'] * count) // 2) * -1
                loses_mood = randint(1, 10) * -1
                
                # Получаем конечную характеристики
                dino.stats['eat'] = edited_stats(dino.stats['eat'], loses_eat)
                dino.stats['mood'] = edited_stats(dino.stats['mood'], loses_mood)

                return_text = t('item_use.eat.bad', lang, item_name=item_name,
                         loses_eat=loses_eat, loses_mood=loses_mood)
    
    elif type_item in ['game_ac', "journey_ac", "collecting_ac", "sleep_ac", 'weapon', 'armor', 'backpack'] and dino:
        action_to_type = {
            'game_ac': 'game', 'journey_ac': 'journey', 
            'collecting_ac': 'collecting', 'sleep_ac': 'sleep',
            'weapon': 'weapon', 'armor': 'armor', 'backpack': 'backpack'
        }
        accessory_type = action_to_type[type_item]
        
        if dino.status == accessory_type:
            # Запрещает менять активный предмет во время совпадающий с его типом активности
            return_text = t('item_use.accessory.no_change', lang)
            use_status = False
        else:
            if dino.activ_items[accessory_type]:
                AddItemToUser(userid, 
                              dino.activ_items[accessory_type]['item_id'], 1, 
                              dino.activ_items[accessory_type]['abilities'])
            if is_standart(item):
                # Защита от вечных аксессуаров
                dino_update_list.append({
                    '$set': {f'activ_items.{accessory_type}': get_item_dict(item['item_id'])}})
            else:
                dino_update_list.append({
                    '$set': {f'activ_items.{accessory_type}': item}})
            
            return_text = t('item_use.accessory.change', lang)
    
    elif type_item == 'recipe':
        materials = {'delete': [], 'edit': {}}
        send_status = False #Проверка может завершится позднее завершения функции, отправим текст самостоятельно

        for iterable_item in data_item['materials']:
            iterable_id: str = iterable_item['item']
            
            if iterable_item['type'] == 'delete':
                materials['delete'].append(get_item_dict(
                    iterable_id))
                
            elif iterable_item['type'] == 'endurance':
                if 'endurance' not in materials['edit']:
                    materials['edit']['endurance'] = {}
                materials['edit']['endurance'][iterable_id] = iterable_item['act'] * count
                
        materials['delete'] = materials['delete'] * count
        deleted_items, not_enough_items = {}, []

        for iterable_item in materials['delete']:
            iter_id = iterable_item['item_id']
            if iter_id not in deleted_items and iter_id not in not_enough_items:
                ret_data_f = CheckItemFromUser(userid, iterable_item, 
                                    materials['delete'].count(iterable_item))
                if ret_data_f['status']:
                    deleted_items[iter_id] = materials['delete'].count(iterable_item)
                else:
                    not_enough_items += [iter_id] * ret_data_f["difference"]

        if not not_enough_items:
            if materials['edit']:
                steps = []
                
                for iterable_key in materials['edit']:
                    for iterable_id in materials['edit'][iterable_key]:
                        steps.append(
                            {"type": 'inv', "name": iterable_id, "data":     
                                {'item_filter': [iterable_id], 
                                'changing_filters': False
                                }, 
                                'message': {'text': t(
                                    'item_use.recipe.consumable_item', lang)
                                            }}
                        )
                await ChooseStepState(edit_craft, userid, 
                                      chatid, lang, steps,
                                      {'count': count, 'materials': materials,
                                       'data_item': data_item
                                       })
            else:
                transmitted_data = {
                    'userid': userid,
                    'chatid': chatid,
                    'lang': lang,
                    'materials': materials,
                    'count': count,
                    'data_item': data_item
                }
                await end_craft(transmitted_data)
        else:
            use_status, send_status = False, True
            return_text = t('item_use.recipe.not_enough_m', lang, materials=counts_items(not_enough_items, lang))
    
    elif data_item['type'] == 'case':
        send_status = False
        drop = data_item['drop_items']; shuffle(drop)
        drop_items = {}
        
        col_repit = random_dict(data_item['col_repit']) #type: int
        for _ in range(col_repit):
            drop_item = None
            while drop_item == None:
                for iterable_data in drop:
                    if randint(1, iterable_data['chance'][1]) <= iterable_data['chance'][0]:
                        drop_item = iterable_data
                        break

            drop_col = random_dict(drop_item['col'])
            if drop_item['id'] in drop_items: drop_items[drop_items['id']] += drop_col
            else: drop_items[drop_items['id']] = drop_col
            
            drop_item_data = get_data(drop_item['id'])
            image = open(f"images/items/{drop_item_data['image']}.png", 'rb')
            
            await bot.send_photo(userid, image, 
                                 t('item_use.case.drop_item', lang), 
                                 parse_mode='Markdown', reply_markup=markups_menu(userid, 'last_menu', lang))
    
    elif data_item['type'] == 'egg':
        user = User(userid)
        dino_limit = user.max_dino_col()['standart']
        use_status = False
        
        if dino_limit['now'] < dino_limit['limit']:
            send_status = False
            buttons = {}
            image, eggs = create_eggs_image()
            code = item_code(item)

            for i in range(3): buttons[f'🥚 {i+1}'] = f'item egg {code} {eggs[i]}'
            buttons = list_to_inline([buttons])

            await bot.send_photo(userid, image, 
                                 t('item_use.egg.egg_answer', lang), 
                                 parse_mode='Markdown', reply_markup=buttons)
            await bot.send_message(userid, 
                                   t('item_use.egg.plug', lang),     
                                   reply_markup=markups_menu(userid, 'last_menu', lang))
        else:
            return_text = t('item_use.egg.egg_limit', lang, 
                            limit=dino_limit['limit'])
    
    if data_item.get('buffs', []) and use_status and use_status and dino:
        # Применяем бонусы от предметов
        return_text += '\n\n'
        
        for bonus in data_item['buffs']:
            if data_item['buffs'][bonus] > 0:
                bonus_name = '+' + bonus
            else: bonus_name = '-' + bonus
            
            dino.stats[bonus] = edited_stats(dino.stats[bonus], 
                         data_item['buffs'][bonus] * count)

            return_text += t(f'item_use.buff.{bonus_name}', lang, 
                            unit=data_item['buffs'][bonus])

    if dino_update_list and dino:
        # Обновляем данные, не связанные с харрактеристиками, например активные предметы
        for i in dino_update_list: dino.update(i)
    
    if dino:
        # Обновляем данные харрактеристик
        upd_values = {}
        dino_now: Dino = Dino(dino._id)
        if dino_now.stats != dino.stats:
            for i in dino_now.stats:
                if dino_now.stats[i] != dino.stats[i]:
                    upd_values['stats.'+i] = dino.stats[i] - dino_now.stats[i]
    
        if upd_values: dino_now.update({'$inc': upd_values})
    
    if use_status:
        if 'abilities' in item and 'uses' in item['abilities']:
            # Если предмет имеет свои харрактеристики, а в частности количество использований, то снимаем их, при том мы знаем что предмета в инвентаре и так count
            if item['abilities']['uses'] != -666:
                res = DowngradeItem(userid, item, count, 'uses', count)
                if not res['status']: 
                    log(f'Item downgrade error - {res} {userid} {item}', 3)
        else:
            # В остальных случаях просто снимаем нужное количество
            if 'abilities' in item:
                res = RemoveItemFromUser(userid, item['item_id'], count)
            else:
                res = RemoveItemFromUser(userid, item['item_id'], 
                                         count, item['abilities'])
            if not res: log(f'Item remove error {userid} {item}', 3)

    return send_status, return_text

async def edit_craft(return_data: dict, transmitted_data: dict):
    materials = transmitted_data['materials']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    items_data = []

    for iterable_key in materials['edit']:
        for item_key, unit in materials['edit'][iterable_key].items():
            item = return_data[item_key]
            ret_data = DowngradeItem(userid, item, 1, 
                                     iterable_key, unit, edit=False)
            items_data.append(ret_data)

    ok = True
    for iterable_data in items_data.copy(): 
        if not iterable_data['status']:
            ok = False
            
            if iterable_data['action'] == 'unit_>_max_characteristic':
                item_name = get_name(iterable_data['item']['item_id'], lang)
                await bot.send_message(chatid, 
                    t('item_use.recipe.enough_characteristics', lang,item_name=item_name), 
                    parse_mode='Markdown', 
                    reply_markup=markups_menu(userid, 'last_menu', lang))
            else:
                log(f'Непредвиденная ошибка в edit_craft -> {iterable_data}\n{items_data}', 3)
    
    if ok:
        for iterable_data in items_data.copy(): 
            if iterable_data['action'] == 'need_remove_item':
                RemoveItemFromUser(userid, iterable_data['item_id'], 
                                   iterable_data['count'], 
                                   iterable_data['item']['abilities'])
            elif iterable_data['action'] == 'edit_item':
                EditItemFromUser(userid, return_data[iterable_data['item']['item_id']], iterable_data['item'], iterable_data['count'])

    await end_craft(transmitted_data)

async def adapter(return_data: dict, transmitted_data: dict):
    del return_data['confirm']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    
    send_status, return_text = await use_item(userid, chatid, lang, transmitted_data['items_data'], **return_data)
    
    if send_status:
        await bot.send_message(chatid, return_text, parse_mode='Markdown', reply_markup=markups_menu(userid, 'last_menu', lang))

async def data_for_use_item(item: dict, userid: int, chatid: int, lang: str):
    item_id = item['item_id']
    data_item = get_data(item_id)
    type_item = data_item['type']
    limiter = 100 # Ограничение по количеству использований за раз
    
    base_item = items.find_one({'owner_id': userid, 'items_data': item})
    transmitted_data = {'items_data': item}
    item_name = get_name(item_id, lang)
    steps = []
    ok = True

    if type(base_item) is None:
        await bot.send_message(chatid, t('item_use.no_item', lang))
    elif type(base_item) is dict:
        
        if 'abilities' in item.keys() and 'uses' in item['abilities']:
            max_count = CalculateAbilitie(base_item['items_data'], base_item['count'], 'uses')
        else: max_count = base_item['count']

        if max_count > limiter: max_count = limiter

        if type_item == 'eat':
            steps = [
                {"type": 'dino', "name": 'dino', "data": {"add_egg": False}, 
                    'message': None},
                {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                    'message': {'text': t('css.wait_count', lang), 
                                'reply_markup': count_markup(max_count)}}
            ]
        elif type_item in ['game_ac', 'sleep_ac', 
                           'journey_ac', 'collecting_ac', 
                           'weapon', 'backpack', 'armor']:
            steps = [
                {"type": 'dino', "name": 'dino', "data": {"add_egg": False}, 
                    'message': None}
            ]
        elif type_item == 'recipe':
            steps = [
                {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                    'message': {'text': t('css.wait_count', lang), 
                                'reply_markup': count_markup(max_count)}}
            ]
        elif type_item == 'weapon':
            steps = [
                {"type": 'dino', "name": 'dino', "data": {"add_egg": False}, 
                    'message': None}
            ]
        elif type_item == 'case':
            steps = [
                {"type": 'int', "name": 'count', "data": {"max_int": max_count}, 
                    'message': {'text': t('css.wait_count', lang), 
                                'reply_markup': count_markup(max_count)}}
            ]
        elif type_item == 'egg':
            steps = []
            
        else:
            ok = False
            await bot.send_message(chatid, t('item_use.cannot_be_used', lang))

        if ok:
            steps.insert(0, {
                "type": 'bool', "name": 'confirm', 
                "data": {'cancel': True}, 
                'message': {
                    'text': t('css.confirm', lang, name=item_name), 'reply_markup': confirm_markup(lang)
                    }
                })
            await ChooseStepState(adapter, userid, chatid, lang, steps, 
                                transmitted_data=transmitted_data)

async def delete_action(return_data: dict, transmitted_data: dict):
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    lang = transmitted_data['lang']
    item = transmitted_data['items_data']
    count = return_data['count']
    item_name = transmitted_data['item_name']
    preabil = {}
    
    if 'abilities' in item: preabil = item['abilities']
    
    res = RemoveItemFromUser(userid, item['item_id'], count, preabil)
    if res:
        await bot.send_message(chatid, t('delete_action.delete', lang,  
                                         name=item_name, count=count), 
                               reply_markup=
                               markups_menu(userid, 'last_menu', lang))
    else:
        await bot.send_message(chatid, t('delete_action.error', lang), 
                               reply_markup=
                               markups_menu(userid, 'last_menu', lang))
        

async def delete_item_action(userid: int, chatid:int, item: dict, lang: str):
    steps = []
    base_item = items.find_one({'owner_id': userid, 'items_data': item})
    transmitted_data = {'items_data': item, 'item_name': ''}
    
    if base_item:
        item_id = item['item_id']
        max_count = base_item['count']
        
        item_name = get_name(item_id, lang)
        transmitted_data['item_name'] = item_name
        
        steps.append({"type": 'int', "name": 'count', 
                      "data": {"max_int": max_count}, 
                      'message': {'text': t('css.wait_count', lang), 
                                  'reply_markup': count_markup(max_count)}}
        )
        steps.insert(0, {
                "type": 'bool', "name": 'confirm', 
                "data": {'cancel': True}, 
                'message': {
                    'text': t('css.delete', lang, name=item_name), 'reply_markup': confirm_markup(lang)
                    }
                })
    
        await ChooseStepState(delete_action, userid, chatid, lang, steps, 
                                transmitted_data=transmitted_data)
    else:
        await bot.send_message(chatid, t('delete_action.error', lang), 
                               reply_markup=
                               markups_menu(userid, 'last_menu', lang))