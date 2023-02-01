# Основной модуль настроек

# Прямой запуск используется для создания файла настроек

# Как модуль предоставляет лишь чтение настроек и доступ к ним

import pymongo
import json
import os
import sys

CONFIG_PATH = 'config.json'

class Config:
    def __init__(self) -> None:
        """Класс настроек бота. Все основные переменные хранятся здесь
        """
        self.bot_token = 'NOTOKEN'
        self.bot_devs = []
        self.temp_dir = 'bot/temp'
        self.logs_dir = 'bot/logs'
        self.active_tasks = True
        self.bot_group_id = 0
        self.mongo_url = 'mongodb://localhost:27017'
        self.debug = False

    def fromJSON(self, js: str) -> None:
        """Десереализует строку в данные

        Args:
            js (str): Строка формата json с парвильной разметкой
        """
        self.__dict__ = json.loads(js)

    def toJSON(self) -> str:
        """Сереализует объект настроек в json строку

        Returns:
            str: сереализованная json строка
        """
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
 
conf = Config()
def check_base():
    with open('bot/json/settings.json', encoding='utf-8') as f: 
        GAME_SETTINGS = json.load(f)

    created_base = mongo_client.list_database_names()
    collections = GAME_SETTINGS['collections']

    for base in collections.keys():
        if base not in created_base:
            database = mongo_client[base]
            for col in collections[base]:
                database.create_collection(col)
    
    print('The databases are checked and prepared for use.')

if __name__ == '__main__':
    with open(CONFIG_PATH, 'w') as f:
        f.write(conf.toJSON())
        sys.exit(f"{CONFIG_PATH} created! Please don't forget to set it up!")
else:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            conf.fromJSON(f.read())

        mongo_client = pymongo.MongoClient(conf.mongo_url)
        check_base() # Проверка базы данных на наличие коллекций
        for way in conf.temp_dir, conf.logs_dir:
            if not os.path.exists(way):
                os.mkdir(way) #Создаёт папку в директории  
                print(f"I didn't find the {way} directory, so I created it.")
    else:
        sys.exit(f"{CONFIG_PATH} missed! Please, run {__name__}")
    
