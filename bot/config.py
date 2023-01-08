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
        self.bot_name = 'NONAME'
        self.bot_devs = []
        self.temp_dir = 'bot/temp'
        self.logs_dir = 'bot/logs'
        self.is_ignore_name = True
        self.bot_group_id = 0
        self.mongo_host = 'localhost'
        self.mongo_port = 27017

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

if __name__ == '__main__':
    with open(CONFIG_PATH, 'w') as f:
        f.write(conf.toJSON())
        sys.exit(f"{CONFIG_PATH} created! Please don't forget to set it up!")    
else:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            conf.fromJSON(f.read())
    else:
        sys.exit(f"{CONFIG_PATH} missed! Please, run {__name__}")

mongo_client = pymongo.MongoClient(conf.mongo_host, conf.mongo_port)
