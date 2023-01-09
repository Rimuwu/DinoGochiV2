# Модуль констант

import json

with open('bot/json/items.json', encoding='utf-8') as f: 
    ITEMS = json.load(f)

with open('bot/json/dino_data.json', encoding='utf-8') as f: 
    DINOS = json.load(f)

with open('bot/json/mobs.json', encoding='utf-8') as f: 
    MOBS = json.load(f)

with open('bot/json/floors_dungeon.json', encoding='utf-8') as f: 
    FLOORS = json.load(f)

with open('bot/json/quests_data.json', encoding='utf-8') as f: 
    QUESTS = json.load(f)

with open('bot/json/settings.json', encoding='utf-8') as f: 
    GAME_SETTINGS = json.load(f)