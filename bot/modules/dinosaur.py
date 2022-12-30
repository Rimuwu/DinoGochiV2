from pprint import pprint

import config
dinosaurs = config.mongo_client.bot.dinosaurs

class Dino:

    def __init__(self, baseid = None) -> None:
        """Создание объекта динозавра."""
        
        # Берём из базы
        if baseid is not None:
            self.id = baseid
            self.data = dinosaurs.find_one({"_id": self.id})
        #Создаём нового динозавра
        else:
            ...

    
    def __str__(self) -> str:
        return f"DinoObj {self.data['name']}"


    def view(self):
        """ Отображает все данные объекта."""

        print('DATA: ', end='')
        pprint(self.data)

    def update(self, update_data: dict[str:dict]):
        """
        {"$set": {'stats.eat': 12}} - установить
        {"$inc": {'stats.eat': 12}} - добавить
        """
        self.data = dinosaurs.update_one({"_id": self.id}, update_data)