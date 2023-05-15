from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.localization import get_data, t
from bot.modules.markup import cancel_markup, confirm_markup
from bot.modules.user import get_frineds, insert_friend_connect, user_name
from bot.modules.states_tools import ChooseCustomState, ChoosePagesState, ChooseConfirmState
from bot.modules.notifications import user_notification
from bot.modules.markup import markups_menu as m
from bot.modules.friend_tools import start_friend_menu

users = mongo_client.bot.users
friends = mongo_client.connections.friends

@bot.message_handler(text='commands_name.friends.add_friend')
async def add_friend(message: Message):
    chatid = message.chat.id
    lang = message.from_user.language_code
    
    text = t('add_friend.var', lang)
    buttons = get_data('add_friend.var_buttons', lang)
    
    inl_buttons = dict(zip(buttons.values(), buttons.keys()))
    markup = list_to_inline([inl_buttons])
    
    await bot.send_message(chatid, text, parse_mode='Markdown', reply_markup=markup)

async def friend_add_handler(message: Message, transmitted_data: dict):
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
    
    await ChooseCustomState(add_friend_end, friend_add_handler, 
                            user_id, chatid, lang, 
                            transmitted_data)

@bot.message_handler(text='commands_name.friends.friends_list')
async def friend_list(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = message.from_user.language_code
    
    await bot.send_message(chatid, t('friend_list.wait'))
    await start_friend_menu(None, userid, chatid, lang, False)


async def adp_requests(data: dict, transmitted_data: dict):
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']

    if data['action'] == 'delete': 
        friends.delete_one(
            {'userid': data['friend'],
             'friendid': userid,
             'type': 'request'
             }
            )

        await bot.send_message(userid, t('requests.decline', lang, user_name=data['name']))
        return {'status': 'edit', 'elements': {'delete': [
            f'✅ {data["key"]}', f'❌ {data["key"]}', data['name']
            ]}}

    elif data['action'] == 'add':
        res = friends.find_one(
            {'userid': data['friend'],
             'friendid': userid,
             'type': 'request'
             }
            )

        if res:
            friends.update_one({'_id': res['_id']}, 
                               {'$set': {'type': 'friends'}})

        await bot.send_message(chatid, t('requests.accept', lang, user_name=data['name']))
        return {'status': 'edit', 'elements': {'delete': [
            f'✅ {data["key"]}', f'❌ {data["key"]}', data['name']
            ]}}
        

async def request_open(userid: int, chatid: int, lang: str):
    requests = get_frineds(userid)['requests']
    options = {}
    a = 0
    
    for friend_id in requests:
        try:
            chat_user = await bot.get_chat_member(friend_id, friend_id)
            friend = chat_user.user
        except: friend = None
        if friend:
            a += 1
            name = user_name(friend)
            if name in options: name = name + str(a)

            options[f"✅ {a}"] = {'action': 'add', 'friend': friend_id, 'key': a, 'name': name}
            
            options[name] = {'action': 'pass'}
            
            options[f"❌ {a}"] = {'action': 'delete', 'friend': friend_id, 'key': a, 'name': name}
    
    await ChoosePagesState(
        adp_requests, userid, chatid, lang, options, 
        horizontal=3, vertical=3,
        autoanswer=False, one_element=False)

@bot.message_handler(text='commands_name.friends.requests')
async def requests_list(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(chatid, t('requests.wait'))
    await request_open(userid, chatid, lang)
    
@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('requests'))
async def requests_callback(call: CallbackQuery):
    chatid = call.message.chat.id
    user_id = call.from_user.id
    lang = call.from_user.language_code
    
    await bot.send_message(chatid, t('requests.wait'))
    await request_open(user_id, chatid, lang)
    
    
async def delete_friend(_: bool, transmitted_data: dict):
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    
    friendid = transmitted_data['friendid']
    
    friends.delete_one({"userid": userid, 'friendid': friendid, 'type': 'friends'})
    friends.delete_one({"friendid": userid, 'userid': friendid, 'type': 'friends'})

    await bot.send_message(chatid, t('friend_delete.delete', lang), 
                           reply_markup=m(userid, 'last_menu', lang))
    
async def adp_delte(friendid: int, transmitted_data: dict):
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    
    transmitted_data['friendid'] = friendid
    
    await ChooseConfirmState(delete_friend, userid, chatid, lang, True, transmitted_data)
    await bot.send_message(chatid, t('friend_delete.confirm', lang,     
                                     name=transmitted_data['key']), 
                           reply_markup=confirm_markup(lang))

@bot.message_handler(text='commands_name.friends.remove_friend')
async def remove_friend(message: Message):
    chatid = message.chat.id
    userid = message.from_user.id
    lang = message.from_user.language_code

    requests = get_frineds(userid)['friends']
    options = {}
    a = 0
    
    for friend_id in requests:
        try:
            chat_user = await bot.get_chat_member(friend_id, friend_id)
            friend = chat_user.user
        except: friend = None
        if friend:
            a += 1
            name = user_name(friend)
            if name in options: name = name + str(a)
            
            options[name] = friend_id

    await bot.send_message(chatid, t('friend_delete.delete_info'))
    await ChoosePagesState(
        adp_delte, userid, chatid, lang, options, 
        autoanswer=False, one_element=True)