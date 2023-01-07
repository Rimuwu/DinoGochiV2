# Модуль загрузки локлизации

import json
import os

from i18n import config, resource_loader, translator


def load() -> None:
    """Настройки локализации
    """
    config.set("file_format", "json")
    config.set("load_path", ["./bot/localization"])
    config.set("filename_format", "{locale}.{format}")
    resource_loader.init_json_loader()

    lang_list = []
    for filename in os.listdir("./bot/localization"):
        with open(f'./bot/localization/{filename}', encoding='utf-8') as f:
            langs_dict = json.load(f)
            for lang_code in langs_dict.keys():
                lang_list.append(lang_code)

    config.set('available_locales', lang_list)

def t(key: str, locale: str = "en", **kwargs) -> str:
    """Возвращает текст на нужном языке

    Args:
        key (str): ключ для текста
        locale (str, optional): код языка. Defaults to "en".
        count (int, optional): числовая часть в переводе. Defaults to 0.

    Returns:
        str: текст на нужном языке
    """
    try:
        return translator.t(key, locale=locale, **kwargs)
    except KeyError:
        return translator.t("no_text_key", locale=locale, **kwargs)

def get_all_locales(key:str, **kwargs):
    """Возвращает текст с ключа key из каждой локализации
    
    Args:
        key (str): ключ для текста

    Returns:
        dict[str]: ключ в словаре - язык
    """
    lang_keys = config.get("available_locales")
    locales_dict = {}

    for locale in lang_keys:
        try:
            locales_dict[locale] = translator.t(key, locale=locale, **kwargs)
        except KeyError:
            locales_dict[locale] = translator.t("no_text_key", locale=locale, **kwargs)
    
    return locales_dict

if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")
else:
    load()
