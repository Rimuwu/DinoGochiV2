
from fuzzywuzzy import fuzz
from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline
from bot.modules.inventory import inventory_pages
from bot.modules.localization import get_data, t
from bot.modules.markup import list_to_keyboard
from bot.modules.states import InventoryStates
from bot.modules.user import get_inventory
from bot.modules.item import item_info

from .states import cancel

users = mongo_client.bot.users
back_button, forward_button = '◀', '▶'

async def send_item_info(item, transmitted_data):
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    
    text, image = item_info(item, lang)
    if image == None:
        await bot.send_message(chatid, text, parse_mode='Markdown')
    else:
        await bot.send_photo(chatid, image, text, parse_mode='Markdown')


async def swipe_page(userid: int, chatid: int):
    """ Панель-сообщение смены страницы инвентаря
    """
    async with bot.retrieve_data(userid, chatid) as data:
        pages = data['pages']
        settings = data['settings']
        items = data['items']
        filters = data['filters']

    keyboard = list_to_keyboard(pages[settings['page']], settings['row'])

    # Добавляем стрелочки
    if len(pages) > 1:
        keyboard.add(*[back_button, t('buttons_name.cancel', settings['lang']), forward_button])
    else:
        keyboard.add(t('buttons_name.cancel', settings['lang']))

    # Генерация текста и меню
    menu_text = t('inventory.menu', settings['lang'], 
                  page=settings['page']+1, col=len(pages))
    text = t('inventory.update_page', settings['lang'])
    buttons = {
        '⏮': 'inventory_menu first_page', '🔎': 'inventory_menu search', 
        '⚙️': 'inventory_menu filters', '⏭': 'inventory_menu end_page'
        }

    if not settings['changing_filters']:
        del buttons['⚙️']

    if filters:
        if settings['changing_filters']:
            buttons['🗑'] = 'inventory_menu clear_filters'
            menu_text += t('inventory.clear_filters', settings['lang'])

    if items:
        buttons['❌🔎'] = 'inventory_menu clear_search'

    inl_menu = list_to_inline([buttons], 4)
    await bot.send_message(chatid, text, reply_markup=keyboard)
    await bot.send_message(chatid, menu_text, reply_markup=inl_menu, parse_mode='Markdown')

async def search_menu(userid: int, chatid: int):
    """ Панель-сообщение поиска
    """
    async with bot.retrieve_data(userid, chatid) as data:
        settings = data['settings']

    menu_text = t('inventory.search', settings['lang'])
    buttons = {'❌': 'inventory_search close'}
    inl_menu = list_to_inline([buttons])

    text = t('inventory.update_search', settings['lang'])
    keyboard = list_to_keyboard([ t('buttons_name.cancel', settings['lang']) ])

    await bot.send_message(chatid, text, reply_markup=keyboard)
    await bot.send_message(chatid, menu_text, 
                           parse_mode='Markdown', reply_markup=inl_menu)
    
async def filter_menu(userid: int, chatid: int):
    """ Панель-сообщение выбора фильтра
    """
    async with bot.retrieve_data(userid, chatid) as data:
        settings = data['settings']
        filters = data['filters']

    menu_text = t('inventory.choice_filter', settings['lang'])
    filters_data = get_data('inventory.filters_data', settings['lang'])
    buttons = {}
    for key, item in filters_data.items():
        name = item['name']
        if list(set(filters) & set(item['keys'])):
            name = "✅" + name

        buttons[name] = f'inventory_filter filter {key}'

    cancel = {'✅': 'inventory_filter close'}
    inl_menu = list_to_inline([buttons, cancel])

    text = t('inventory.update_filter', settings['lang'])
    keyboard = list_to_keyboard([ t('buttons_name.cancel', settings['lang']) ])

    if 'edited_message' in settings and settings['edited_message']:
        try:
            await bot.edit_message_text(menu_text, chatid, settings['edited_message'], reply_markup=inl_menu, parse_mode='Markdown')
        except: pass
    else:
        await bot.send_message(chatid, text, reply_markup=keyboard)
        msg = await bot.send_message(chatid, menu_text, 
                            parse_mode='Markdown', reply_markup=inl_menu)
        
        async with bot.retrieve_data(
            userid, chatid) as data: data['settings']['edited_message'] = msg.id

async def start_inv(userid: int, chatid: int, lang: str, 
                    type_filter: list = [], item_filter: list = [], 
                    start_page: int = 0, changing_filters: bool = True,
                    function = None, transmitted_data=None):
    """ Функция запуска инвентаря
    """
    
    if not transmitted_data:
        transmitted_data = {}
    
    if 'userid' not in transmitted_data: transmitted_data['userid'] = userid
    if 'chatid' not in transmitted_data: transmitted_data['chatid'] = chatid
    if 'lang' not in transmitted_data: transmitted_data['lang'] = lang
    
    user_settings = users.find_one({'userid': userid}, {'settings': 1})
    if user_settings: inv_view = user_settings['settings']['inv_view']
    else: inv_view = [2, 3]

    invetory = get_inventory(userid)
    pages, row, items_data, names = inventory_pages(invetory, lang, inv_view, type_filter, item_filter)

    if not pages:
        await bot.send_message(chatid, t('inventory.null', lang))
    else:
        try:
            async with bot.retrieve_data(userid, chatid) as data:
                old_function = data['function']
                old_transmitted_data = data['transmitted_data']
            
            if old_function:
                function = old_function
            if old_transmitted_data:
                transmitted_data = old_transmitted_data
        except: 
            # Если не передана функция, то вызывается функция информация о передмете
            function = send_item_info
            
        await bot.set_state(userid, InventoryStates.Inventory, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['pages'] = pages
            data['items_data'] = items_data
            data['names'] = names
            data['filters'] = type_filter
            data['items'] = item_filter

            data['settings'] = {'view': inv_view, 'lang': lang, 
                                'row': row, 'page': start_page,
                                'changing_filters': changing_filters
                                }
            
            data['function'] = function
            data['transmitted_data'] = transmitted_data

        await swipe_page(userid, chatid)

async def open_inv(userid: int, chatid: int):
    """ Внутренняя фунция для возврата в инвентарь
    """
    await bot.set_state(userid, InventoryStates.Inventory, chatid)
    await swipe_page(userid, chatid)

@bot.message_handler(text='commands_name.profile.inventory', is_authorized=True, state=None)
async def open_inventory(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    await start_inv(userid, chatid, lang)

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
        await start_inv(chatid, chatid, lang)
    
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
        await start_inv(chatid, chatid, lang)


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
        await start_inv(userid, chatid, lang, item_filter=searched)
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
            
        await start_inv(userid, chatid, lang, filters)
    
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