import json
import time

import translators
from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

from_l = 'ru'
ro_l = 'en'

with open(f'../bot/localization/{from_l}.json', encoding='utf-8') as f: 
    main_lang = json.load(f) # type: dict

with open(f'../bot/localization/{ro_l}.json', encoding='utf-8') as f: 
    add_lang = json.load(f) # type: dict

def trs(text: str, trs='bing'):
    # spl = text.split('{')
    # args_lst = []
    # for i in text:
    #     if i.startswith('{') and i.endswith('}'):
            
    
    if text:
        try:
            lang = detect(text)
        except: lang = 'emoji'
        if lang != 'en':
            # try:
            ret = translators.translate_text(text, 
                from_language=from_l, 
                to_language=ro_l, translator=trs)
            print(text, 'translate', trs, ret)
            return ret
            # except Exception as e: print('Ошибка перевода', '-', e)
    return text

def trs_circul(s, c=0):
    if c >= 10: return s

    try: return trs(s, 'yandex')
    except: 
        try:  return trs(s, 'google')
        except:
            try: return trs(s, 'deepl')
            except: 
                try: return trs(s, 'alibaba')
                except:
                    try: return trs(s, 'bing')
                    except:
                        c += 1
                        print('ПОВТОРНАЯ ТРАНСЛЯЦИЯ')
                        return trs_circul(s, c)
    

def dict_string(s):
    
    if type(s) == str: return trs_circul(s)
    elif  type(s) == int: return s
    elif type(s) == list:
        lst = []
        for i in s: lst.append(dict_string(i))
        return lst
    elif type(s) == dict:
        dct = {}
        for key, value in s.items(): 
            if key not in ['data', 'callback', 'inline_menu']:
                dct[key] = dict_string(value)
            else: dct[key] = value
        return dct
    return s

def save(data):
    with open(f'{ro_l}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if not add_lang: add_lang[ro_l] = {}

for key, value in main_lang['ru'].items():
    if key not in add_lang[ro_l]:
        add_lang[ro_l][key] = dict_string(value)
        save(add_lang)