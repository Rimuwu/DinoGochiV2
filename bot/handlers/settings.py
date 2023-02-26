from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.localization import t
from bot.modules.markup import markups_menu as m

users = mongo_client.bot.users

