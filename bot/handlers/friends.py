from bot import config

from telebot import types
from bot.exec import bot
from bot.modules.localization import t, get_data
from bot.modules.data_format import list_to_inline
from bot.modules.states_tools import ChooseIntState

@bot.message_handler(text='commands_name.friends.add_friend')
async def add_friend(message: types.Message):
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    text = t('add_friend.var', lang)
    buttons = get_data('add_friend.var_buttons', lang)
    
    inl_buttons = dict(zip(buttons.values(), buttons.keys()))
    markup = list_to_inline([inl_buttons])
    
    await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)

async def id_adapter(userid: bool, transmitted_data: dict):
    # Проверка есть ли в базе, есть ли в друзьях
    ...
    


@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('add_friend'))
async def add_friend_callback(call: types.CallbackQuery):
    chatid = call.message.chat.id
    user_id = call.from_user.id
    lang = call.from_user.language_code
    messageid = call.message.id
    
    code = call.data.split()[1]
    
    if code == 'id':
        await ChooseIntState(id_adapter, user_id, chatid, lang, 1, 0)
        
    elif code == 'message':
        ...

    