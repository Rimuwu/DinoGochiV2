# Модуль загрузки локлизации

from i18n import resource_loader
from i18n import translator
from i18n import config

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
