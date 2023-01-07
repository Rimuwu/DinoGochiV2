# Модуль загрузки локлизации

import json
import os
from bot.modules.logs import console_message

languages = {}
available_locales = []

def load() -> None:
    """Загрузка локализации"""

    for filename in os.listdir("./bot/localization"):
        with open(f'./bot/localization/{filename}', encoding='utf-8') as f:
            languages_f = json.load(f)

        for l_key in languages_f.keys():
            available_locales.append(l_key)
            languages[l_key] = languages_f[l_key]

    console_message(f"Загружено {len(languages.keys())} файла(ов) локализации.", 1)

def t(key: str, locale: str = "en", **kwargs) -> str:
    """Возвращает текст на нужном языке

    Args:
        key (str): ключ для текста
        locale (str, optional): код языка. Defaults to "en".

    Returns:
        str: текст на нужном языке
    """
    if locale not in available_locales:
        locale = 'en' # Если язык не найден, установить тот что точно есть

    text = languages[locale]
    for way_key in key.split('.'):
        if way_key in text.keys():
            text = text[way_key]
        else:
            return languages[locale]["no_text_key"].format(key=key)

    if type(text) == str: #Если текс, добавляем туда переменные
        text.format(**kwargs)
        
    return text

def get_all_locales(key:str, **kwargs):
    """Возвращает текст с ключа key из каждой локализации
    
    Args:
        key (str): ключ для текста

    Returns:
        dict[str]: ключ в словаре - код языка
    """
    locales_dict = {}

    for locale in available_locales:
        locales_dict[locale] = t(key, locale, **kwargs)

    return locales_dict

if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")
else:
    load()
