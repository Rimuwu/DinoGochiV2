import random
from random import randint
from time import time

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.data_format import user_name
from bot.modules.dinosaur import insert_dino
from bot.modules.notifications import user_notification
from bot.taskmanager import add_task

dinosaurs = mongo_client.bot.dinosaurs
random.seed(1)

# Переменные изменения харрактеристик
HEAL_CHANGE = 1, 2
EAT_CHANGE = 1, 2
GAME_CHANGE = 1, 2
ENERGY_CHANGE = 1, 2
MOOD_CHANGE = 1, 2

# Переменные порогов
CRITICAL_ENERGY = 10
CRITICAL_EAT = 20
HIGH_EAT = 80
LOW_EAT = 40
HIGH_MOOD = 50

REPEAT_MINUTS = 2
# Переменные вероятности
P_HEAL = 0.05 * REPEAT_MINUTS
P_EAT_SLEEP = 0.1 * REPEAT_MINUTS
P_EAT = 0.075 * REPEAT_MINUTS
P_GAME = 0.1 * REPEAT_MINUTS
P_ENERGY = 0.04 * REPEAT_MINUTS
P_MOOD1 = 0.2 * REPEAT_MINUTS
P_MOOD2 = 0.3 * REPEAT_MINUTS
P_MOOD3 = 0.05 * REPEAT_MINUTS
P_HEAL_EAT = 0.1 * REPEAT_MINUTS

def mutate_dino_stat(dino, key, value):
    st = dino['stats'][key]
    if st + value > 100: value = 100 - st
    elif st + value < 0: value = -st
    
    dinosaurs.update_one({'_id': dino['_id']}, 
                         {'$inc': {f'stats.{key}': value}})

async def main_checks():
    """Главная проверка динозавров
    """

    dinos = dinosaurs.find({})
    for dino in dinos:
        if dino['status'] == 'inactive': continue
        is_sleeping = dino['status'] == 'sleep'

        # условие выполнения для понижения здоровья
        # если здоровье и еда находятся на критическом уровне
        if dino['stats']['energy'] <= CRITICAL_ENERGY and dino['stats']['eat'] <= CRITICAL_EAT and random.uniform(0, 1) <= P_HEAL:
            mutate_dino_stat(dino, 'heal', randint(*HEAL_CHANGE)*-1)

        # условие выполнения для понижения питания
        # если динозавр спит, вероятность P_EAT_SLEEP
        # если динозавр не спит, вероятность P_EAT
        if (random.uniform(0, 1) <= P_EAT_SLEEP and is_sleeping) or (random.uniform(0, 1) <= P_EAT and not is_sleeping):
            mutate_dino_stat(dino, 'eat', randint(*EAT_CHANGE)*-1)

        # условие выполнения если динозавр не играет
        if dino['status'] != 'game' and random.uniform(0, 1) <= P_GAME:
            mutate_dino_stat(dino, 'game', randint(*GAME_CHANGE)*-1)

        # условие выполнения для восстановления энергии
        # если динозавр не спит
        if not(is_sleeping) and (random.uniform(0, 1) <= P_ENERGY):
            mutate_dino_stat(dino, 'energy', randint(*ENERGY_CHANGE)*-1)


        # elif dino['stats']['game'] < 40 and dino['stats']['game'] > 10:
        #     if dino['stats']['mood'] > 0 and random.uniform(0, 1) <= P_MOOD1:
        #         mutate_dino_stat(dino, 'mood', randint(*MOOD_CHANGE))

        # elif dino['stats']['game'] < 10:
        #     if dino['stats']['mood'] > 0 and random.uniform(0, 1) <= P_MOOD2:
        #         mutate_dino_stat(dino, 'mood', randint(*MOOD_CHANGE))


        # условие выполнения для питания и восстановления здоровья
        # если динозавр не испытывает голод, не находится в критическом запасе энергии, настроение находится выше среднего
        if dino['stats']['eat'] > HIGH_EAT and dino['stats']['energy'] > CRITICAL_ENERGY and dino['stats']['mood'] > HIGH_MOOD:
            if random.uniform(0, 1) <= P_HEAL_EAT:
                mutate_dino_stat(dino, 'heal', randint(1, 4))
                mutate_dino_stat(dino, 'eat', randint(0, 1))

        # if dino['stats']['eat'] <= LOW_EAT and dino['stats']['eat'] != 0:
        #     if dino['stats']['mood'] > 0 and random.uniform(0, 1) <= P_MOOD3:
        #         mutate_dino_stat(dino, 'mood', randint(*MOOD_CHANGE))

if __name__ != '__main__':
    if conf.active_tasks:
        add_task(main_checks, REPEAT_MINUTS * 60.0, 5.0)