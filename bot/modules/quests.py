from bot.const import QUESTS
from bot.modules.localization import t, get_data
from random import choice

def create_quest(complexity: int, qtype: str='', lang: str='en'):
    """complexity - [1, 5]
    """
    quests = []
    
    if not qtype:
        types = ['feed', 'collecting', 'fishing', 'journey', 'game', 'kill', 'get']
        qtype = choice(types)
    
    for quest in QUESTS:
        if quest['type'] == qtype and quest['complexity'] == complexity:
            quests.append(quest)

    if quests:
        quest_data = choice(quests)
        quest = {
            'reward': {'money': 0, 'items': []},
            'complexity': complexity,
            'type': qtype,
            'time': 0,
        }

        quest['author'] = choice(get_data('quests.authors', lang))
        quest['name'] = choice(get_data(f'quests.{qtype}', lang))

        return quest
    else:
        return False