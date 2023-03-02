from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.localization import get_data, t
from bot.modules.markup import back_menu
from bot.modules.markup import markups_menu as m
from bot.modules.user import User
from bot.modules.data_format import user_name
from asyncio import sleep

users = mongo_client.bot.users
management = mongo_client.bot.management

@bot.message_handler(text='buttons_name.back', is_authorized=True)
async def back_buttom(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    back_m = back_menu(userid)

    user_dict = users.find_one(
           {'userid': userid}, {'last_markup': 1}
        )
    
    if user_dict:
        if user_dict.get('last_markup') == 'dino_tavern_menu':
            management.update_one({'_id': 'in_tavern' }, {'$pull': {'users': userid}})

    text = t(f'back_text.{back_m}', lang)
    await bot.send_message(message.chat.id, text, 
                           reply_markup=m(userid, back_m, lang) )

@bot.message_handler(text='commands_name.settings_menu', is_authorized=True)
async def settings_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    prf_view_ans = get_data('profile_view.ans', lang)

    user = users.find_one({'userid': userid})
    if user:
        settings = user['settings']
        text = t('menu_text.settings', lang, 
                notif=settings['notifications'], 
                vis_faq=settings['faq'],
                profile_view=prf_view_ans[settings['profile_view']-1],
                inv_view=f"{settings['inv_view'][0]} | {settings['inv_view'][1]}"
                )
        text = text.replace('True', '✅').replace('False', '❌')

        await bot.send_message(message.chat.id, text, 
                               reply_markup=m(userid, 'settings_menu', lang))

@bot.message_handler(text='commands_name.profile_menu', is_authorized=True)
async def profile_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.profile', lang), 
                           reply_markup=m(userid, 'profile_menu', lang))
    
@bot.message_handler(text='commands_name.friends_menu', is_authorized=True)
async def friends_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.friends', lang), 
                           reply_markup=m(userid, 'friends_menu', lang))

@bot.message_handler(text='commands_name.profile.market', is_authorized=True)
async def market_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.market', lang), 
                           reply_markup=m(userid, 'market_menu', lang))

@bot.message_handler(text='commands_name.actions_menu', is_authorized=True)
async def actions_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    await bot.send_message(message.chat.id, t('menu_text.actions', lang), 
                           reply_markup=m(userid, 'actions_menu', lang))
    
@bot.message_handler(text='commands_name.dino-tavern_menu', is_authorized=True)
async def tavern_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    user = User(userid)
    friends = user.get_friends()['friends']
    text = ''

    management.update_one({'_id': 'in_tavern'}, {'$push': {'users': userid}})
    users_in_tavern = management.find_one({'_id': 'in_tavern'})['users'] #type: ignore
    friends_in_tavern = set(friends) & set(users_in_tavern)

    await bot.send_message(message.chat.id, t('menu_text.dino_tavern.info', lang), reply_markup=m(userid, 'dino_tavern_menu', lang))
    msg = await bot.send_message(message.chat.id, t('menu_text.dino_tavern.friends', lang))
    text = t('menu_text.dino_tavern.friends2', lang)

    if len(friends_in_tavern):
        text += '\n'
        for friendid in friends_in_tavern:
            friendChat = await bot.get_chat_member(friendid, friendid)
            friend = friendChat.user
            if friend:
                text += f' ● {user_name(friend)}\n'
                text_to_friend = t('menu_text.dino_tavern.went', 
                                   friend.language_code, 
                                   name=user_name(message.from_user))
                await bot.send_message(friendid, text_to_friend)
                await sleep(0.5)
    else:
        text += '❌'

    await bot.edit_message_text(text=text, chat_id=userid, message_id=msg.message_id)