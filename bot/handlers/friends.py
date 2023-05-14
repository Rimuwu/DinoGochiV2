from telebot.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.localization import get_data, t
from bot.modules.markup import cancel_markup
from bot.modules.user import get_frineds, insert_friend_connect, user_name
from bot.modules.states_tools import ChooseCustomState
from bot.modules.notifications import user_notification
from bot.modules.markup import markups_menu as m

users = mongo_client.bot.users

@bot.message_handler(text='commands_name.friends.add_friend')
async def add_friend(message: Message):
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    text = t('add_friend.var', lang)
    buttons = get_data('add_friend.var_buttons', lang)
    
    inl_buttons = dict(zip(buttons.values(), buttons.keys()))
    markup = list_to_inline([inl_buttons])
    
    await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)

async def friend_handler(message: Message, transmitted_data: dict):
    code = transmitted_data['code']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']

    content = str(message.text)
    text, status, friendid = '', False, 0

    if code == 'id':
        # Обработчик, проверяющий является ли контекст сообщения id
        if content.isdigit(): friendid = int(content)
        else: text = t('add_friend.check.nonint', lang, userid=userid)

    elif code == 'message':
        # Обработчик, проверяющий является ли сообщение пересылаемым кем то
        if message.forward_from: 
            friendid = message.forward_from.id
        else: text = t('add_friend.check.forward', lang)

    if friendid:
        result = users.find_one({'userid': friendid})
        if result:
            if userid == friendid:
                text = t('add_friend.check.notyou', lang)
            else: status = True
        else:
            text = t('add_friend.check.nonbase', lang)

    if not status: await bot.send_message(chatid, text)
    return status, friendid
    
async def add_friend_end(friendid: int, transmitted_data: dict):
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    user_name = transmitted_data['user_name']
    
    frineds = get_frineds(userid)
    for act_type in ['friends', 'requests']:
        if friendid in frineds[act_type]:
            text = t(f'add_friend.check.{act_type}', lang)
            await bot.send_message(chatid, text)
            return 
    else:
        insert_friend_connect(userid, friendid, 'request')
        text = t('add_friend.correct', lang)
        await bot.send_message(chatid, text, 
                               reply_markup=m(userid, 'last_menu', lang))
        
        await user_notification(friendid, 'send_request', lang, user_name=user_name)

@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('add_friend'))
async def add_friend_callback(call: CallbackQuery):
    chatid = call.message.chat.id
    user_id = call.from_user.id
    lang = call.from_user.language_code
    
    code = call.data.split()[1]
    transmitted_data = {'code': code, 'user_name': user_name(call.from_user)}
    
    text = t(f'add_friend.var_messages.{code}', lang)
    await bot.send_message(chatid, text, reply_markup=cancel_markup(lang))
    
    await ChooseCustomState(add_friend_end, friend_handler, 
                            user_id, chatid, lang, 
                            transmitted_data)

    