from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS as GS
from bot.exec import bot
from bot.modules.data_format import escape_markdown, list_to_inline
from bot.modules.item import counts_items
from bot.modules.localization import get_data, t, get_lang
from bot.modules.markup import cancel_markup
from bot.modules.markup import markups_menu as m
from bot.modules.referals import connect_referal, create_referal
from bot.modules.states_tools import ChooseCustomState, ChooseStringState
from bot.modules.user import take_coins

users = mongo_client.bot.users
referals = mongo_client.connections.referals

@bot.message_handler(text='commands_name.referal.code', is_authorized=True)
async def code(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
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


async def create_custom_code(code: str, transmitted_data: dict):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    
    if take_coins(userid, GS['referal']['custom_price'], True):
        create_referal(userid, code)

        iambot = await bot.get_me()
        bot_name = iambot.username

        url = f'https://t.me/{bot_name}/?start={code}'
        text = t('referals.code', lang, code=code, url=url)
    else:
        text = t('referals.custom_code.no_coins', lang)

    await bot.send_message(chatid, text, parse_mode='Markdown', 
                        reply_markup=m(userid, 'last_menu', lang, True))

async def custom_handler(message: Message, transmitted_data: dict):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    
    code = escape_markdown(str(message.text))
    status = False
    text = ''
    
    if len(code) > 10:
        text = t('referals.custom_code.max_len', lang)
    if len(code) == 0:
        text = t('referals.custom_code.min_len', lang)
    else:
        res = referals.find_one({'code': code})
        if res:
            text = t('referals.custom_code.found_code', lang)
        else: status = True

    if not status:
        await bot.send_message(chatid, text, parse_mode='Markdown')
    return status, code

@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('generate_referal'), private=True)
async def generate_code(call: CallbackQuery):
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = get_lang(call.from_user.id)
    action = call.data.split()[1]
    
    if not referals.find_one({'ownerid': userid}):
        if action == 'random':
            code = create_referal(userid)[1]
            
            iambot = await bot.get_me()
            bot_name = iambot.username

            url = f'https://t.me/{bot_name}/?start={code}'
            await bot.send_message(chatid, t('referals.code', lang, 
                                    code=code, url=url), parse_mode='Markdown', reply_markup=m(userid, 'last_menu', lang, True))
            
        elif action == 'custom':
            await bot.send_message(chatid, 
                                   t('referals.custom_code.start', lang), parse_mode='Markdown', reply_markup=cancel_markup(lang))
            await ChooseCustomState(create_custom_code, custom_handler, 
                                    userid, chatid, lang)
    else:
        await bot.send_message(chatid, t('referals.have_code', lang))


@bot.message_handler(textstart='commands_name.referal.my_code')
async def my_code(message: Message):
    """ Кнопка - мой код ...
    """
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id
    
    referal = referals.find_one({'userid': userid})
    if referal:
        code = referal['code']
        referal_find = referals.find(
            {'code': code, 'type': 'sub'})

        uses = len(list(referal_find))

        iambot = await bot.get_me()
        bot_name = iambot.username
        url = f'https://t.me/{bot_name}/?start={code}'
        
        await bot.send_message(chatid, t('referals.my_code', lang, 
                                code=code, url=url, uses=uses), parse_mode='Markdown')

async def check_code(code: str, transmitted_data: dict):
    lang = transmitted_data['lang']
    userid = transmitted_data['userid']
    chatid = transmitted_data['chatid']
    
    coins = GS['referal']['coins']
    items = GS['referal']['items']
    names = counts_items(items, lang)
    
    result = connect_referal(code, userid)
    text = t(f'referals.enter_code.{result}', lang, coins=coins, items=names)
    await bot.send_message(chatid, text, parse_mode='Markdown', 
                        reply_markup=m(userid, 'last_menu', lang, True))

@bot.message_handler(text='commands_name.referal.enter_code', is_authorized=True)
async def enter_code(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id

    ref = referals.find_one({'userid': userid, 'type': 'sub'})
    if not ref:
        await bot.send_message(chatid, t('referals.enter_code.start', lang), parse_mode='Markdown', reply_markup=cancel_markup(lang))
        await ChooseStringState(check_code, userid, chatid, lang)
    else:
        await bot.send_message(chatid, t('referals.enter_code.have_code', lang), parse_mode='Markdown')