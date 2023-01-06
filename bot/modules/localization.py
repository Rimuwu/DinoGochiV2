# Модуль загрузки локлизации

from i18n import resource_loader
from i18n import translator
from i18n import config
import json
from bot.modules.logs import LogFuncs
import os

config.set("file_format", "json")
config.set("load_path", ["./bot/localization"])
config.set("filename_format", "{locale}.{format}")
config.set("locale", "en")
resource_loader.init_json_loader()

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


class Localization:

    def __init__(self) -> None:
        self.languages = self.load_languages()

    def __str__(self) -> str:
        return f"Object localization(s) {', '.join(self.languages.keys())}"

    
    def load_languages(self):
        ''' Загрузка фалов локализации
            Загружает все словари c локализацией в один словарь.
        '''
        languages = {}

        for filename in os.listdir("bot/localization"): # берём всем фалы из папки
            with open(f'bot/localization/{filename}', encoding='utf-8') as f:
                languages_f = json.load(f)

            for l_key in languages_f.keys(): #добавляем в словарь
                languages[l_key] = languages_f[l_key]

        LogFuncs.console_message(f"Загружено {len(languages.keys())} файла(ов) локализации.", 1)
        return languages

    
    def get_language_dict(self, lang:str = None) -> dict:
        ''' Получить словарь определённого языка или все сразу.
        '''

        if lang:
            if lang in self.languages.keys():
                return self.languages[lang]

            else:
                raise Exception("Localization with such a key is not found!")
        else:
            return self.languages
    
    def get_all_text_from_key(self, text_key:str) -> dict:
        ''' Получить все варианты локализации по одному ключу
            Пример -> 
            >>> func("language_name")
            >>> {'ru': 'Русский', 'en': 'English'}
        '''

        all_text_from_lkey = {}

        for lang_key in self.languages.keys():
            if lang_key != 'null':
                all_text_from_lkey[lang_key] = self.languages[lang_key][text_key]

        return all_text_from_lkey
    
    def get_text(self, language: str, text_key: str, dp_text_key: str = None) -> str | dict:
        ''' Получить текст по ключу

            dp_text_key - дополнительный ключ для словаря
        '''

        if language not in self.languages.keys():
            language = 'en' # Если язык не найден, установить тот что точно есть

        if text_key not in self.languages[language].keys():
            return self.languages[language]["no_text_key"].format(key=text_key) #есди ключ текста не найден, то оповещаем об этом юзера

        if dp_text_key == None:
            return self.languages[language][text_key]

        else:
            if type(self.languages[language][text_key]) == dict:
                if dp_text_key not in self.languages[language][text_key].keys():
                    return self.languages[language]["no_dp_text_key"]
                else:
                    return self.languages[language][text_key][dp_text_key]
            else:
                return self.languages[language][text_key]


if __name__ == '__main__':
    raise Exception("This file cannot be launched on its own!")
