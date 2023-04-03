from bot.const import ITEMS
import json

directory = 'data.json'
data = {}

for key, item in ITEMS['items'].items():
    if 'descriptionru' in item:
        del item['descriptionru']
    if 'descriptionen' in item:
        del item['descriptionen']
    
    del item['name']
    
    data[int(key)] = item

with open(directory, 'w', encoding='utf-8') as file:
    json.dump(data, file, sort_keys=True, indent=2, ensure_ascii=False)

print(1)