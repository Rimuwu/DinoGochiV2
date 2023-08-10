from asyncio import sleep

from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str, user_name, escape_markdown)
from bot.modules.item import AddItemToUser, counts_items, get_name, item_info
from bot.modules.localization import get_data, get_lang, t
from bot.modules.market import (add_product, create_seller, delete_product,
                                buy_product, product_ui, seller_ui)
from bot.modules.market_chose import (pr_edit_description, pr_edit_name,
                                      prepare_add, prepare_data_option,
                                      prepare_delete_all, prepare_edit_price, pr_edit_image, buy_item, promotion_prepare)
from bot.modules.markup import answer_markup, cancel_markup, count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import (ChooseOptionState, ChooseStepState,
                                      prepare_steps)
from bot.modules.user import premium

users = mongo_client.bot.users
management = mongo_client.bot.management
tavern = mongo_client.connections.tavern
sellers = mongo_client.market.sellers
items = mongo_client.bot.items
products = mongo_client.market.products

async def create_adapter(return_data, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']

    name = return_data['name']
    name = escape_markdown(name)
    description = return_data['description']
    create_seller(userid, name, description)

    await bot.send_message(chatid, t('market_create.create', lang), 
                           reply_markup=m(userid, 'seller_menu', lang), parse_mode='Markdown')

@bot.message_handler(text='commands_name.seller_profile.create_market', is_authorized=True)
async def create_market(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id

    res = sellers.find_one({'owner_id': userid})
    user = users.find_one({'userid': userid})

    if res or not user:
        await bot.send_message(message.chat.id, t('menu_text.seller', lang), 
                           reply_markup=m(userid, 'market_menu', lang))
    elif user['lvl'] < 2:
        await bot.send_message(message.chat.id, t('market_create.lvl', lang))
    else:
        transmitted_data = {}
        steps = [
            {
             "type": 'str', "name": 'name', "data": {'max_len': 50, 'min_len': 3}, 
             "translate_message": True,
             'message': {
                'text': "market_create.name",
                'reply_markup': cancel_markup(lang)}
            },
            {
             "type": 'str', "name": 'description', "data": {'max_len': 500}, 
             "translate_message": True,
             'message': {
                'text': "market_create.description",
                'reply_markup': cancel_markup(lang)}
            }
        ]

        await ChooseStepState(create_adapter, userid, chatid, 
                              lang, steps, 
                              transmitted_data=transmitted_data)

@bot.message_handler(text='commands_name.seller_profile.my_market', is_authorized=True)
async def my_market(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id

    res = sellers.find_one({'owner_id': userid})
    if res:
        text, markup, image = seller_ui(userid, lang, True)
        await bot.send_photo(chatid, image, text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(text='commands_name.seller_profile.add_product', is_authorized=True)
async def add_product_com(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id

    options = {
        "🍕 ➡ 🪙": 'items_coins',
        "🪙 ➡ 🍕": 'coins_items',
        "🍕 ➡ 🍕": 'items_items',
        "🍕 ➡ ⏳": 'auction'
    }

    b_list = list(options.keys())
    markup = list_to_keyboard(
        [b_list, t('buttons_name.cancel', lang)], 2
    )

    await bot.send_message(chatid, t('add_product.options_info', lang), reply_markup=markup)
    await ChooseOptionState(prepare_data_option, userid, chatid, lang, options)

@bot.message_handler(text='commands_name.seller_profile.my_products', is_authorized=True)
async def my_products(message: Message):
    userid = message.from_user.id
    lang = get_lang(message.from_user.id)
    chatid = message.chat.id

    user_prd = list(products.find({'owner_id': userid}, {'_id': 1}))
    if user_prd:
        for i in user_prd:

            text, markup = product_ui(lang, i['_id'], True)
            await bot.send_message(chatid, text, reply_markup=markup, parse_mode='Markdown')
            await sleep(1)
    else:
        text = t('no_products', lang)
        await bot.send_message(chatid, text,  parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('product_info'), private=True)
async def product_info(call: CallbackQuery):
    call_data = call.data.split()
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = get_lang(call.from_user.id)

    call_type = call_data[1]
    alt_id = call_data[2]

    if call_type == 'delete':
        status = await delete_product(None, alt_id)

        if status: text = t('product_info.delete', lang)
        else: text = t('product_info.error', lang)

        markup = list_to_inline([])
        await bot.edit_message_text(text, chatid, call.message.id, reply_markup=markup, parse_mode='Markdown')
    else:
        product = products.find_one({'alt_id': alt_id})
        if product:
            if call_type == 'edit_price':
                await prepare_edit_price(userid, chatid, lang, alt_id)

            elif call_type == 'add':
                await prepare_add(userid, chatid, lang, alt_id)

            elif call_type == 'items':
                for item in product['items']:
                    text, image = item_info(item, lang)
                    await bot.send_message(chatid, text, parse_mode='Markdown')

            elif call_type == 'buy':
                await buy_item(userid, chatid, lang, product, user_name(call.from_user))

            elif call_type == 'info':
                text, markup = product_ui(lang, product['_id'], 
                                          product['owner_id'] == userid)
                await bot.send_message(chatid, text, reply_markup=markup, parse_mode='Markdown')

            elif call_type == 'promotion':
                await promotion_prepare(userid, chatid, lang, product['_id'], call.message.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('seller'), private=True)
async def seller(call: CallbackQuery):
    call_data = call.data.split()
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = get_lang(call.from_user.id)

    call_type = call_data[1]
    owner_id = call_data[2]

    # Кнопки вызываемые владельцем
    if call_type == 'cancel_all':
        await prepare_delete_all(userid, chatid, lang, call.message.id)
    elif call_type == 'edit_text':
        await pr_edit_description(userid, chatid, lang, call.message.id)
    elif call_type == 'edit_name':
        await pr_edit_name(userid, chatid, lang, call.message.id)
    elif call_type == 'edit_image':
        if premium(userid):
            await pr_edit_image(userid, chatid, lang, call.message.id)
        else:
            await bot.send_message(chatid, t('no_premium', lang))

    # Кнопки вызываемые не владельцем
    elif call_type == 'info':
        my_status = int(owner_id) == userid
        text, markup, image = seller_ui(userid, lang, False)
        await bot.send_photo(chatid, image, text, parse_mode='Markdown', reply_markup=markup)

    elif call_type == 'all':
        user_prd = list(products.find({'owner_id': int(owner_id)}, {'_id': 1}))
        if user_prd:
            for i in user_prd:
                text, markup = product_ui(lang, i['_id'], False)
                await bot.send_message(chatid, text, reply_markup=markup, parse_mode='Markdown')
                await sleep(1)