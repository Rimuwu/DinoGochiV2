# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.item import get_name, get_item_dict, get_data
from bot.config import mongo_client
from bot.modules.user import User
from bot.modules.donation import get_donations

dinosaurs = mongo_client.bot.dinosaurs

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    user_id = message.from_user.id

    user = User(user_id)

    await bot.send_message(message.from_user.id, str(await get_donations()))