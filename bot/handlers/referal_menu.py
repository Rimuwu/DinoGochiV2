from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS as GS
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.localization import get_data, t
from bot.modules.markup import cancel_markup, confirm_markup
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import (ChooseConfirmState, ChooseCustomState,
                                      ChoosePagesState)
from bot.modules.user import get_frineds, insert_friend_connect, user_name, create_referal

users = mongo_client.bot.users
referals = mongo_client.connections.referals

@bot.message_handler(text='commands_name.referal.code', is_authorized=True)
async def code(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    if not referals.find_one({'ownerid': userid}):
        price = GS['referal']['custom_price']
        
        text = t('referals.generate', lang, price=price)
        buttons = get_data('referals.var_buttons', lang)
    
        inl_buttons = dict(zip(buttons.values(), buttons.keys()))
        markup = list_to_inline([inl_buttons])
        
        await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)
    else:
        await bot.send_message(message.chat.id, t('referals.have_code', lang))


@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('generate_referal'))
async def generate_code(call: CallbackQuery):
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = call.from_user.language_code
    action = call.data.split()[1]
    
    if not referals.find_one({'ownerid': userid}):
        if action == 'random':
            code = create_referal(userid)[1]
            
            iambot = await bot.get_me()
            bot_name = iambot.username

            url = f'https://t.me/{bot_name}/?start={code}'
            await bot.send_message(chatid, t('referals.code', lang, 
                                             code=code, url=url), parse_mode='Markdown')
            
        elif action == 'custom':
            ...
    
    else:
        await bot.send_message(chatid, t('referals.have_code', lang))
    