import json
from pprint import pprint

from bot.modules.localization import get_all_locales
from bot.modules.data_format import random_dict

with open('bot/json/items.json', encoding='utf-8') as f: items_data = json.load(f)['items']

def get_data(itemid: str) -> dict:
    """Получение данных из json"""

    # Проверяем еть ли предмет с таким ключём в items.json
    if itemid in items_data.keys():
        return items_data[itemid]
    else:
        raise Exception(f"The subject with ID {itemid} does not exist.")

class ItemBase:

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        ''' Создание объекта Item

            Получаем в класс либо id предмета либо формата {"item_id": string, "abilities": dict}\n
            abilities - не обязателен.

            Пояснение:
              >>> Стандартный предмет - предмет никак не изменённый пользователем, сгенерированный из базы.
              >>> abilities - словарь с индивидуальными харрактеристиками предмета, прочность, использования и тд.
              >>> preabil - используется только для предмета создаваемого из базы, используется для создания нестандартного предмета.

        '''

        if item_id != 0: # Получаем стандартный предмет, если есть только id
            self.id = str(item_id)

        elif item_data != {}: # Предмет от пользователя, есть id и возможно abilities
            self.id = str(item_data['item_id'])
            if 'abilities' in item_data.keys():
                preabil = item_data['abilities']
            
        else:
            raise Exception(f"An empty object cannot be created.")

        self.data = get_data(self.id)
        self.names = self.get_names()
        self.user_data = self.get_item_dict(preabil=preabil)
        self.is_standart = self.check_standart()
    
    def __str__(self) -> str:
        return f"Item{self.data['type'].capitalize()}Object {self.names}"

    
    def get_names(self) -> dict:
        """Внесение всех имён в данные предмета"""

        # Получаем словарь со всеми альтернативные имена предметов из локализации
        items_names = get_all_locales('items_names')
        data_names = self.data['name']
        name = {}

        # Проверяем есть ли ключ с языком в данных и вносим новые.
        # Приоритетом является имя из items.json
        for lang_code in items_names:
            if lang_code not in data_names.keys():
                if self.id in items_names[lang_code]:
                    name[lang_code] = items_names[lang_code][self.id]
                    self.data['name'][lang_code] = items_names[lang_code][self.id]
            
            else:
                name[lang_code] = data_names[lang_code]
        
        return name
    
    def get_item_dict(self, preabil: dict = {}) -> dict:
        ''' Создание словаря, хранящийся в инвентаре пользователя.\n

            Примеры: 
                Просто предмет
                  >>> f(12)
                  >>> {'item_id': "12"}

                Предмет с предустоновленными 
                  >>> f(30, {'uses': 10})
                  >>> {'item_id': "30", 'abilities': {'uses': 10}}

        '''
        d_it = {'item_id': self.id, 'abilities': {}}

        if 'abilities' in self.data.keys():
            abl = {}
            for k in self.data['abilities'].keys():

                if type(self.data['abilities'][k]) == int:
                    abl[k] = self.data['abilities'][k]

                elif type(self.data['abilities'][k]) == dict:
                    abl[k] = random_dict(self.data['abilities'][k])

            d_it['abilities'] = abl

        if preabil != {}:
            if 'abilities' in d_it.keys():
                for ak in d_it['abilities']:
                    if ak in preabil.keys():

                        if type(preabil[ak]) == int:
                            d_it['abilities'][ak] = preabil[ak]

                        elif type(preabil[ak]) == dict:
                            d_it['abilities'][ak] = random_dict(preabil[ak])

        return d_it
    
    def check_standart(self) -> bool:
        """Определяем ли стандартный ли предмет*.

        Для этого проверяем есть ли у него свои харрактеристик.\n
        Если их нет - значит он точно стандартный.\n
        Если они есть и не изменены - стандартный.
        """

        if list(self.user_data.keys()) == ['item_id']:
            return True
        else:
            if 'abilities' in self.user_data.keys():
                if self.user_data['abilities'] == self.data['abilities']:
                    return True
                else:
                    return False
            else:
                return True


    def view(self) -> None:
        """ Отображает все данные объекта."""
        
        print(f'ID: {self.id}')
        print(f'NAMES: {self.names}')

        print("USER_DATA: ", end='')
        pprint(self.user_data)

        print("DATA: ", end='')
        pprint(self.data)


class EatItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class EggItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class AccessoryItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class MaterialItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class RecipeItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class WeaponItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class AmmunitionItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class BackpackItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)
    
class ArmorItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class FreezingItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class DefrostingItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class CaseItem(ItemBase):

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}) -> None:
        super().__init__(item_id, item_data, preabil)

class CreateItem:

    def __init__(self, item_id: str | int = 0, item_data: dict = {}, preabil: dict = {}):
        self.id = item_id
        self.item_data = item_data
        self.preabil = preabil

        if item_id != 0:
            self.data = get_data(str(self.id))
        else:
            self.data = get_data(item_data['item_id'])

    def new(self):
        data = (self.id, self.item_data, self.preabil)
        item_type = self.data['type']
        class_dict = {
            '+eat': EatItem, 'egg': EggItem,

            'game_ac': AccessoryItem, 'journey_ac': AccessoryItem,
            'unv_ac': AccessoryItem,  'hunt_ac': AccessoryItem,

            'material': MaterialItem, 'recipe': RecipeItem,

            'weapon': WeaponItem,  'ammunition': AmmunitionItem,
            'backpack': BackpackItem, 'armor': ArmorItem,

            'freezing': FreezingItem, 'defrosting': DefrostingItem,

            'case': CaseItem
        }

        if item_type in class_dict.keys():
            return class_dict[item_type](*data)
        else:
            return ItemBase(*data)

if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")