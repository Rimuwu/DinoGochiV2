# Тестовые команды

from telebot.types import Message
from bot.exec import bot
from bot.modules.item import get_name, get_item_dict, get_data
from bot.config import mongo_client
from bot.modules.user import User

dinosaurs = mongo_client.bot.dinosaurs

@bot.message_handler(commands=['test'])
async def test_command(message: Message):
    user_id = message.from_user.id

    user = User(user_id)
    print(user.get_friends())

@bot.message_handler(start_with='commands_name.actions.dino_button')
async def test_command2(message: Message):
    user_id = message.from_user.id
    print('ok')



    