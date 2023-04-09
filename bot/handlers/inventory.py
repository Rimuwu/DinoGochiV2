
from fuzzywuzzy import fuzz
from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.inventory_tools import (InventoryStates, back_button, filter_menu,
                                   forward_button, search_menu, start_inv,
                                   swipe_page, send_item_info)
from bot.modules.item import decode_item
from bot.modules.localization import get_data, t
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import data_for_use

users = mongo_client.bot.users

async def cancel(message):
    await bot.send_message(message.chat.id, "❌", 
          reply_markup=m(message.from_user.id, 'last_menu', message.from_user.language_code))
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reset_data(message.from_user.id,  message.chat.id)

@bot.message_handler(text='commands_name.profile.inventory', is_authorized=True, state=None)
async def open_inventory(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    await start_inv(None, userid, chatid, lang)

@bot.message_handler(state=InventoryStates.Inventory, is_authorized=True)
async def inventory(message: Message):
    userid = message.from_user.id
    chatid = message.chat.id
    content = message.text

    async with bot.retrieve_data(userid, chatid) as data:
        pages = data['pages']
        items_data = data['items_data']
        names = data['names']
        page = data['settings']['page']

        function = data['function']
        transmitted_data = data['transmitted_data']

    if content == back_button:
        if page == 0: page = len(pages) - 1
        else: page -= 1

        async with bot.retrieve_data(userid, chatid) as data: data['settings']['page'] = page
        await swipe_page(userid, chatid)
        
    elif content == forward_button:
        if page >= len(pages) - 1: page = 0
        else: page += 1

        async with bot.retrieve_data(userid, chatid) as data: data['settings']['page'] = page
        await swipe_page(userid, chatid)

    elif content in names:
        await function(items_data[content], transmitted_data)
    else:
        await cancel(message)
    
@bot.callback_query_handler(state=InventoryStates.Inventory, func=lambda call: call.data.startswith('inventory_menu'))
async def inv_callback(call: CallbackQuery):
    call_data = call.data.split()[1]
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = call.from_user.language_code
    
    if call_data == 'search':
        # Активирует поиск
        await bot.set_state(userid, InventoryStates.InventorySearch, chatid)
        await search_menu(chatid, chatid)
    
    elif call_data == 'clear_search':
        # Очищает поиск
        await start_inv(None, chatid, chatid, lang)
    
    elif call_data == 'filters':
        # Активирует настройку филтров
        await bot.set_state(userid, InventoryStates.InventorySetFilters, chatid)
        await filter_menu(chatid, chatid)

    elif call_data in ['end_page', 'first_page']:
        # Быстрый переходи к 1-ой / полседней странице
        page = 0
        async with bot.retrieve_data(userid, chatid) as data:
            pages = data['pages']

        if call_data == 'first_page':
            page = 0
        elif call_data == 'end_page':
            page = len(pages) - 1

        async with bot.retrieve_data(userid, chatid) as data: data['settings']['page'] = page
        await swipe_page(chatid, chatid)
    
    elif call_data == 'clear_filters':
        # Очищает фильтры
        await start_inv(None, chatid, chatid, lang)

@bot.callback_query_handler(func=lambda call: call.data.startswith('item'))
async def item_callback(call: CallbackQuery):
    call_data = call.data.split()
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = call.from_user.language_code
    item = decode_item(call_data[2])
    
    if item:
        if call_data[1] == 'info':
            await send_item_info(item, {'chatid': chatid, 'lang': lang})
        elif call_data[1] == 'use':
            await data_for_use(item, userid, chatid, lang)
        elif call_data[1] == 'delete':
            ...
        elif call_data[1] == 'exchange':
            ...

# Поиск внутри инвентаря
@bot.callback_query_handler(state=InventoryStates.InventorySearch, 
                            func=lambda call: call.data.startswith('inventory_search'))
async def search_callback(call: CallbackQuery):
    call_data = call.data.split()[1]
    chatid = call.message.chat.id
    userid = call.from_user.id

    if call_data == 'close':
        # Данная функция не открывает новый инвентарь, а возвращает к меню
        await bot.set_state(userid, InventoryStates.Inventory, chatid)
        await swipe_page(userid, chatid)

@bot.message_handler(state=InventoryStates.InventorySearch, is_authorized=True)
async def seacr_message(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    content = message.text
    searched = []

    async with bot.retrieve_data(userid, chatid) as data:
        names = data['names']
        items_data = data['items_data']

    for item in names:
        name = item[2:]
        tok_s = fuzz.token_sort_ratio(content, name)
        ratio = fuzz.ratio(content, name)

        if tok_s >= 60 or ratio >= 60:
            item_id = items_data[item]['item_id']
            if item_id not in searched:
                searched.append(item_id)

    if searched:
        await start_inv(None, userid, chatid, lang, item_filter=searched)
    else:
        await bot.send_message(chatid, t('inventory.search_null', lang))


#Фильтры
@bot.callback_query_handler(state=InventoryStates.InventorySetFilters, func=lambda call: call.data.startswith('inventory_filter'))
async def filter_callback(call: CallbackQuery):
    call_data = call.data.split()
    chatid = call.message.chat.id
    userid = call.from_user.id
    lang = call.from_user.language_code

    if call_data[1] == 'close':
        # Данная функция не открывает новый инвентарь, а возвращает к меню
        async with bot.retrieve_data(userid, chatid) as data:
            filters = data['filters']
            settings = data['settings']
            
        if 'edited_message' in settings:
            await bot.delete_message(chatid, settings['edited_message'])
            
        await start_inv(None, userid, chatid, lang, filters)
    
    if call_data[1] == 'filter':
        async with bot.retrieve_data(userid, chatid) as data:
            filters = data['filters']
        
        filters_data = get_data('inventory.filters_data', lang)
        if call_data[2] == 'null':
            async with bot.retrieve_data(userid, chatid) as data:
                data['filters'] = []

            if filters:
                await filter_menu(userid, chatid)
        
        else:
            data_list_filters = filters_data[call_data[2]]['keys']

            if data_list_filters[0] in filters:
                for i in data_list_filters:
                    filters.remove(i)
            else:
                for i in data_list_filters:
                    filters.append(i)

            async with bot.retrieve_data(userid, chatid) as data:
                data['filters'] = filters

            await filter_menu(userid, chatid)