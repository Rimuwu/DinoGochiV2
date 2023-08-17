import json
import time
import random

import emoji

import translators
from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

from_l = 'ru'
ro_l = 'en'

with open(f'./{from_l}.json', encoding='utf-8') as f: 
    main_lang = json.load(f) # type: dict

with open(f'./{ro_l}.json', encoding='utf-8') as f: 
    add_lang = json.load(f) # type: dict

def trs(text: str, trs='bing'):
    from_language = from_l
    if trs == 'myMemory' and from_language == 'ru': from_language = 'ru-RU'

    if text:
        try:
            lang = detect(text)
        except: lang = 'emoji'

        if lang not in ['en', 'it']:
            ret = translators.translate_text(text, 
                from_language=from_language,
                to_language=ro_l, translator=trs) 
            print("\n#TEXT#", text, '\n#translatore#', trs, '\nRETURN TEXT#', ret, '\nlang', lang)
            return ret
    return text

def trs_circul(s):
    # myMemory bing papago modernMt reverso
    res = s
    for i in range(700):
        translators = ['bing', 'modernMt', 'myMemory'] # 'myMemory',  reverso !papago!
        trans = 'bing'

        try:
            try:
                trans = random.choice(translators)
                res = trs(s, trans)
                break
            except:
                translators.remove(trans)
                trans = random.choice(translators)
                res = trs(s, trans)
                break
        except Exception as E: print(E)

        r_t = random.uniform(0, 1)
        time.sleep(r_t)
    return res

k_list = ['*', '`']

def dict_string(s, s_key):

    if type(s) == str:
        if len(s) == 1: return s

        if s_key not in ['data', 'callback', 'inline_menu']:
            repl_words = {
                '(n!)': {'text': '\n', 'translate': False},
                '(nn!)': {'text': '\n\n', 'translate': False},
            }
            s = s.replace('\n\n', '(nn!)')
            s = s.replace('\n', '(n!)')

            word, st = '', False
            i, new_text = '', ''

            for i in emoji.emoji_list(s):
                k_name = f'({len(repl_words)}{len(repl_words)}!)'
                repl_words[k_name] = {
                    'text': i['emoji'],
                    'translate': False
                }
                s = s.replace(i['emoji'], k_name)
                word = ''

            word, st = '', False

            for i in s:
                if i == '{':
                    st = True
                    word += i

                if i == '}':
                    st = False
                    word += i

                    word = word[1:]

                    k_name = f'({len(repl_words)}{len(repl_words)}!)'
                    repl_words[k_name] = {
                        'text': word,
                        'translate': False
                    }
                    s = s.replace(word, k_name)

                    word = ''

                if st: word += i

            for i in s:
                if i in k_list and st: 
                    st = False
                    translate_st = True
                    word += i
                    end_word = word[1:-1]

                    if len(end_word) == 1: translate_st = False

                    k_name = f'({len(repl_words)}{len(repl_words)}!)'
                    repl_words[k_name] = {
                        'text': end_word,
                        'translate': translate_st,
                        'sml': i
                    }
                    s = s.replace(word, k_name)
                    word = ''

                elif i in k_list and not st: st = True
                if st: word += i

            if i != s: new_text = trs_circul(s)

            for i in range(4):
                for key, data in repl_words.items():

                    if data['translate']:
                        if len(data['text']) > 3 and data['text'][1] == '(' and data['text'][-2] == ')': txt = data['text']
                        else:
                            txt = trs_circul(data['text'])
                    else: txt = data['text']
                    
                    if 'sml' in data:
                        txt = data['sml'] + txt + data['sml']

                    new_text = new_text.replace(key, txt) #type: ignore

            return new_text

    elif  type(s) == int: return s

    elif type(s) == list:
        lst = []
        for i in s: lst.append(dict_string(i, s_key))
        return lst

    elif type(s) == dict:
        dct = {}
        for key, value in s.items(): 
            if key not in ['data', 'callback']:
                dct[key] = dict_string(value, s_key)
            else: dct[key] = value
        return dct
    return s

def save(data):
    with open(f'{ro_l}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if not add_lang: add_lang[ro_l] = {}

start = time.time()

for key, value in main_lang['ru'].items():
    if key not in add_lang[ro_l]:
        add_lang[ro_l][key] = dict_string(value, key)
        save(add_lang)

print('END translate', time.time() - start)