from telebot.types import Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import (list_to_inline, list_to_keyboard,
                                     seconds_to_str, user_name)
from bot.modules.item import AddItemToUser, counts_items, get_name
from bot.modules.localization import get_data, get_lang, t
from bot.modules.market import (add_product, create_seller,
                                generate_sell_pages, product_ui, seller_ui, generate_items_pages)
from bot.modules.markup import answer_markup, cancel_markup, count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import (ChooseOptionState, ChooseStepState,
                                      prepare_steps)
from bot.modules.market_chose import prepare_data_option

users = mongo_client.bot.users
management = mongo_client.bot.management
tavern = mongo_client.connections.tavern
sellers = mongo_client.market.sellers
items = mongo_client.bot.items


async def create_adapter(return_data, transmitted_data):
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']

    name = return_data['name']
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
             "type": 'str', "name": 'name', "data": {'max_len': 50}, 
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