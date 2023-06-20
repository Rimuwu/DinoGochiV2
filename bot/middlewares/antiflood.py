# Система антифлуда

from telebot.asyncio_handler_backends import BaseMiddleware, SkipHandler
from telebot.types import Message
from bot.exec import bot
from bot.config import mongo_client

DEFAULT_RATE_LIMIT = 1
users = mongo_client.bot.users

class AntifloodMiddleware(BaseMiddleware):

    throttle_dict = {}

    def __init__(self, limit=DEFAULT_RATE_LIMIT):
        self.last_time = {}
        self.limit = limit
        self.update_types = ['message']

    async def pre_process(self, message: Message, data: dict):
        if not message.from_user.id in self.last_time:
            self.last_time[message.from_user.id] = message.date
            return
        if message.date - self.last_time[message.from_user.id] < self.limit:
            return SkipHandler()
        self.last_time[message.from_user.id] = message.date

    async def post_process(self, message, data, exception):
        users.update_one({'userid': message.from_user.id}, {'$set': {'last_message_time': message.date}})
        await bot.send_chat_action(message.chat.id, 'typing', 1)

bot.setup_middleware(AntifloodMiddleware())