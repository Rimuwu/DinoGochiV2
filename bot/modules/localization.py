# Модуль загрузки локлизации

import json
import os
from bot.modules.logs import log

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

    log(f"Загружено {len(languages.keys())} файла(ов) локализации.", 1)

def t(key: str, locale: str = "en", **kwargs) -> str:
    """Возвращает текст на нужном языке

    Args:
        key (str): ключ для текста
        locale (str, optional): код языка. Defaults to "en".

    Returns:
        str: текст на нужном языке
    """

    def get_text(locale_dict: dict, key: str):
        text = locale_dict

        for way_key in key.split('.'):
            if way_key.isdigit():
                way_key = int(way_key)

            if way_key in text.keys():
                text = text[way_key]
            else:
                return languages[locale]["no_text_key"].format(key=key)

        if type(text) == str:
            if text.startswith('#@') and text.endswith('@#'): # type: ignore
                # Рекурсия дабы создать возможность делать ссылки на локализацию
                # Пример ссылки #@language_name@#
                text = text[2:][:-2]
                text = get_text(locale_dict, text)

        return text

    if locale not in available_locales:
        locale = 'en' # Если язык не найден, установить тот что точно есть
    
    locale_dict = languages[locale]
    data = get_text(locale_dict, key)

    if type(data) == str: #Добавляем переменные в текс
        data = data.format(**kwargs) # type: ignore
        
    return data # type: ignore

def get_all_locales(key: str, **kwargs) -> dict:
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
