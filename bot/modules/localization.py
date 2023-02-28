# Модуль загрузки локлизации

import json
import os
from typing import Any
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


def get_data(key: str, locale: str = "en") -> Any:
    """Возвращает данные локализации

    Args:
        key (str): ключ
        locale (str, optional): язык. Defaults to "en".

    Returns:
        str | dict: возвращаемое
    """
    if locale not in available_locales:
        locale = 'en' # Если язык не найден, установить тот что точно есть
    
    localed_data = languages[locale]

    for way_key in key.split('.'):
        if way_key.isdigit():
            way_key = int(way_key)

        if way_key in localed_data.keys():
            localed_data = localed_data[way_key]
        else:
            return languages[locale]["no_text_key"].format(key=key)
        
    return localed_data


def t(key: str, locale: str = "en", formating: bool = True, **kwargs) -> str:
    """Возвращает текст на нужном языке

    Args:
        key (str): ключ для текста
        locale (str, optional): код языка. Defaults to "en".

    Returns:
        str: текст на нужном языке
    """
    text = str(get_data(key, locale)) #Добавляем переменные в текст
    if formating:
        text = text.format(**kwargs)

    return text


def tranlate_data(data: list | dict, locale: str = "en", key_prefix = '', **kwargs) -> Any:
    """ Переводит текст внутри словаря или списка
        
        Args:
        key_prefix - добавляет ко всем ключам префикс

        Example:
            > data = ['button1', 'button2']
            > key_prefix = 'commands_name.'
        >> ['commands_name.button1', 'commands_name.button2']

        Чтобы отменить префикс, добавьте "noprefix." перед элементом.
        Чтобы отменить перевод добавьте "notranslate." перед элементом.
    """

    if type(data) == list:

        def tr_list(lst):
            result_list = []
            for element in lst:
                if type(element) == str:
                    if key_prefix:
                        if not element.startswith('noprefix.') and not element.startswith('notranslate.'):
                            element = key_prefix + element
                        else:
                            element = element.replace('noprefix.', '')

                    if not element.startswith('notranslate.'):
                        result_list.append(t(element, locale, **kwargs))
                    else:
                        result_list.append(
                            element.replace('notranslate.', ''))
                else:
                    result_list.append(tr_list(element))

            return result_list

        result_list = tr_list(data)
        return result_list

    elif type(data) == dict:
        result_dict = {}
        for key, value in data:
            if key_prefix:
                if not value.startswith('noprefix.'):
                    value = key_prefix + value
                else:
                    value.replace('noprefix.', '')

            result_dict[key] = t(value, locale, **kwargs)

        return result_dict

def get_all_locales(key: str, **kwargs) -> dict:
    """Возвращает текст с ключа key из каждой локализации
    
    Args:
        key (str): ключ для текста

    Returns:
        dict[str]: ключ в словаре - код языка
    """
    locales_dict = {}

    for locale in available_locales:
        locales_dict[locale] = get_data(key, locale, **kwargs)

    return locales_dict

if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")
else:
    load()
