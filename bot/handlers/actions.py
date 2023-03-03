from telebot.types import Message, CallbackQuery

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.localization import t
from bot.modules.markup import markups_menu as m
from bot.modules.user import User

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs


@bot.message_handler(textstart='commands_name.actions.dino_button')
async def edit_dino_buttom(message: Message):
    user_id = message.from_user.id
    user = User(user_id)
    dinos = user.get_dinos()
    data_names = {}

    for element in dinos:
        txt = f'🦕 {element.name}' #type: ignore
        data_names[txt] = f'edit_dino {element.alt_id}'
    
    inline = list_to_inline([data_names], 2)
    await bot.send_message(user_id, 
                           t('edit_dino_button.edit', message.from_user.language_code), 
                           reply_markup=inline)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_dino'))
async def answer_edit(call: CallbackQuery):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    user = User(user_id)

    message = call.message
    data = call.data.split()[1]

    await bot.delete_message(user_id, message.id)
    dino = dinosaurs.find_one({'alt_id': data}, {'_id': 1, 'name': 1})
    if dino:
        user.update({'$set': {'settings.last_dino': dino['_id']}})
        await bot.send_message(user_id, 
                               t('edit_dino_button.susseful', lang, 
                               name=dino['name']),
                               reply_markup=m(user_id, 'actions_menu', lang, True)
                              )
        
async def short_sleep():
    ...

async def long_sleep():
    ...

@bot.message_handler(textstart='commands_name.actions.put_to_bed')
async def put_to_bed(message: Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code

    user = User(user_id)
    last_dino = user.get_last_dino()

    # if last_dino:
        



