from asyncio import sleep

from telebot.types import Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS as GS
from bot.exec import bot
from bot.modules.data_format import user_name, seconds_to_str
from bot.modules.item import counts_items
from bot.modules.localization import get_data, t
from bot.modules.markup import back_menu
from bot.modules.markup import markups_menu as m
from bot.modules.user import User
from bot.modules.statistic import get_now_statistic
from datetime import datetime, timezone, timedelta

users = mongo_client.bot.users
management = mongo_client.bot.management

@bot.message_handler(text='buttons_name.back', is_authorized=True)
async def back_buttom(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    back_m = back_menu(userid)
    
    # Переделать таверну полностью

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
                profile_view=prf_view_ans[settings['profile_view']-1],
                inv_view=f"{settings['inv_view'][0]} | {settings['inv_view'][1]}"
                )
        text = text.replace('True', '✅').replace('False', '❌')

        await bot.send_message(message.chat.id, text, 
                               reply_markup=m(userid, 'settings_menu', lang))

@bot.message_handler(text='commands_name.settings.settings_page_2', is_authorized=True)
async def settings2_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    user = users.find_one({'userid': userid})
    if user:
        my_name = None
        settings = user['settings']
        
        if 'my_name' in settings: my_name = settings['my_name']
        if not my_name: my_name = t('owner', lang)
        
        text = t('menu_text.settings2', lang, my_name=my_name)

        await bot.send_message(message.chat.id, text, 
                               reply_markup=m(userid, 'settings2_menu', lang))

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
    friends = user.get_friends['friends']
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
                try:
                    await bot.send_message(
                        friendid, text_to_friend)
                except:
                    await sleep(0.5)
                    try: 
                        await bot.send_message(
                            friendid, text_to_friend)
                    except: pass
    else:
        text += '❌'

    await bot.edit_message_text(text=text, chat_id=userid, message_id=msg.message_id)

@bot.message_handler(text='commands_name.profile.about', is_authorized=True)
async def about_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code

    iambot = await bot.get_me()
    bot_name = iambot.username
    col_u, col_d, col_i, update_time = '?', '?', '?', '?'
    
    statistic = get_now_statistic()
    if statistic:
        col_u = statistic['users']
        col_d = statistic['dinosaurs']
        col_i = statistic['items']
        
        create = statistic['_id'].generation_time
        now = datetime.now(timezone.utc)
        delta: timedelta = now - create
        
        update_time = seconds_to_str(delta.seconds, lang, True)
    
    await bot.send_message(message.chat.id, t(
        'menu_text.about', lang, bot_name=bot_name,
        col_u=col_u, col_d=col_d, col_i=col_i, update_time=update_time
        ), 
                           reply_markup=m(userid, 'about_menu', lang),
                           parse_mode='Markdown'
                           )

@bot.message_handler(text='commands_name.friends.referal', is_authorized=True)
async def referal_menu(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    
    coins = GS['referal']['coins']
    items = GS['referal']['items']
    award_items = GS['referal']['award_items']
    lvl = GS['referal']['award_lvl']
    
    award_text = counts_items(award_items, lang, t('menu_text.referal_separator', lang))
    names = counts_items(items, lang)
    
    await bot.send_message(message.chat.id, t(
                'menu_text.referal', lang, 
                coins=coins, items=names, 
                award_text=award_text, lvl=lvl), 
                parse_mode='Markdown',
                reply_markup=m(userid, 'referal_menu', lang))