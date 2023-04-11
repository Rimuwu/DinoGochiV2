from telebot.asyncio_handler_backends import State, StatesGroup

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import chunks, list_to_inline
from bot.modules.inline import item_info_markup
from bot.modules.item import (decode_item, get_data, get_name, is_standart,
                              item_code, item_info)
from bot.modules.localization import get_data as get_loc_data
from bot.modules.localization import t
from bot.modules.markup import list_to_keyboard
from bot.modules.markup import markups_menu as m
from bot.modules.user import get_inventory
from bot.modules.logs import log

users = mongo_client.bot.users
back_button, forward_button = '◀', '▶'

class InventoryStates(StatesGroup):
    Inventory = State() # Состояние открытого инвентаря
    InventorySearch = State() # Состояние поиска в инвентаре
    InventorySetFilters = State() # Состояние настройки фильтров в инвентаре

def inventory_pages(items: list[dict], lang: str = 'en', 
                    view: list[int] = [2, 3], type_filter: list[str] = [],
                    item_filter: list[str] = []):
    """ Создаёт и сортируем страницы инвентаря

    type_filter - если не пустой то отбирает предметы по их типу
    item_filter - если не пустой то отбирает предметы по id
    !: Предмет добавляется если соответствует хотя бы одному фильтру

    item: {
        items_data: {
            item_id: str
            abilities: dict (может отсутствовать)
        },
        count: int
    }
    """
    items_data, items_names = {}, []
    horizontal, vertical = view

    for base_item in items:
        item = base_item['item'] # Сам предмет
        data = get_data(item['item_id']) # Дата из json
        add_item = False
        
        # Если предмет найден в базе
        if data:
            # Проверка на соответсвие фильтров
            if not (type_filter or item_filter):
                # Фильтры пустые
                add_item = True
            else:
                try:
                    if data['type'] in type_filter: add_item = True
                    if item['item_id'] in item_filter: add_item = True
                except: log(str(data), 2)
                
            # Если предмет показывается на страницах
            if add_item:
                name = get_name(item['item_id'], lang)
                count = base_item['count']
                standart = is_standart(item)

                if standart: end_name = f"{name} x{count}"
                else:
                    code = item_code(item, False)
                    end_name = f"{name} ({code}) x{count}"
                items_data[end_name] = item

    items_names = list(items_data.keys())
    items_names.sort()

    # Создаёт список, со структурой инвентаря
    pages = chunks(chunks(items_names, horizontal), vertical)

    # Добавляет пустые панели для поддержания структуры
    for i in pages:
        if len(i) != vertical:
            for _ in range(vertical - len(i)):
                i.append([' ' for _ in range(horizontal)])
    
    # Нужно, чтобы стрелки корректно отображались
    if horizontal < 3 and len(pages) > 1: horizontal = 3
    return pages, horizontal, items_data, items_names
    
async def send_item_info(item: dict, transmitted_data: dict):
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']
    
    text, image = item_info(item, lang)
    markup = item_info_markup(item, lang)
    if image is None:
        await bot.send_message(chatid, text, 'Markdown',
                            reply_markup=markup)
    else:
        await bot.send_photo(chatid, image, text, 'Markdown', 
                            reply_markup=markup)

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
        del buttons['🔎']

    if filters:
        if settings['changing_filters'] and settings['changing_filters']:
            buttons['🗑'] = 'inventory_menu clear_filters'
            menu_text += t('inventory.clear_filters', settings['lang'])

    if items and settings['changing_filters']:
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
    filters_data = get_loc_data('inventory.filters_data', settings['lang'])
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

async def start_inv(function, userid: int, chatid: int, lang: str, 
                    type_filter: list = [], item_filter: list = [], 
                    start_page: int = 0, changing_filters: bool = True,
                    transmitted_data: dict | None = None):
    """ Функция запуска инвентаря
    """
    if not transmitted_data: transmitted_data = {}
    
    if 'userid' not in transmitted_data: transmitted_data['userid'] = userid
    if 'chatid' not in transmitted_data: transmitted_data['chatid'] = chatid
    if 'lang' not in transmitted_data: transmitted_data['lang'] = lang
    
    user_settings = users.find_one({'userid': userid}, {'settings': 1})
    if user_settings: inv_view = user_settings['settings']['inv_view']
    else: inv_view = [2, 3]

    invetory = get_inventory(userid)
    pages, row, items_data, names = inventory_pages(invetory, lang, inv_view, type_filter, item_filter)
    
    # if function is None:function = send_item_info

    if not pages:
        await bot.send_message(chatid, t('inventory.null', lang))
        return False, 'cancel'
    else:
        try:
            async with bot.retrieve_data(userid, chatid) as data:
                old_function = data['function']
                old_transmitted_data = data['transmitted_data']
            
            if old_function: function = old_function
            if old_transmitted_data: transmitted_data = old_transmitted_data
        except: 
            # Если не передана функция, то вызывается функция информация о передмете
            if function is None: function = send_item_info
            
        await bot.set_state(userid, InventoryStates.Inventory, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['pages'] = pages
            data['items_data'] = items_data
            data['names'] = names
            data['filters'] = type_filter
            data['items'] = item_filter

            data['settings'] = {'view': inv_view, 'lang': lang, 
                                'row': row, 'page': start_page,
                                'changing_filters': changing_filters}

            data['function'] = function
            data['transmitted_data'] = transmitted_data

        await swipe_page(userid, chatid)
        return True, 'inv'

async def open_inv(userid: int, chatid: int):
    """ Внутренняя фунция для возврата в инвентарь
    """
    await bot.set_state(userid, InventoryStates.Inventory, chatid)
    await swipe_page(userid, chatid)