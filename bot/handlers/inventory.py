
from telebot.types import Message

from bot.exec import bot
from bot.modules.inventory import inventory_pages
from bot.modules.localization import t
from bot.modules.markup import list_to_keyboard
from bot.modules.states import AlternativeStates
from bot.modules.user import get_inventory
from bot.modules.data_format import list_to_inline

back_button, forward_button = '◀', '▶'

async def swipe_page(chatid: int, lang: str, page: int, pages: list, row: int):
    keyboard = list_to_keyboard(pages[page], row)

    # Добавляем стрелочки
    if len(pages) > 1:
        keyboard.add(*[back_button, t('buttons_name.cancel', lang), forward_button])
    else:
        keyboard.add(t('buttons_name.cancel', lang))
    
    # Генерация текста и меню
    menu_text = t('inventory.menu', lang, page=page+1, col=len(pages))
    text = t('inventory.update_page', lang)
    inl_menu = list_to_inline(
        [
        {'⏮': 'inventory_menu first_page', '🔎': 'inventory_menu search', 
         '🧸': 'inventory_menu filters', '⏭': 'inventory_menu end_page'}
        ], 4
    )

    await bot.send_message(chatid, text, reply_markup=keyboard)
    await bot.send_message(chatid, menu_text, reply_markup=inl_menu)

@bot.message_handler(text='commands_name.profile.inventory', is_authorized=True)
async def open_inventory(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id

    invetory = get_inventory(userid)
    pages, row, items_data, names = inventory_pages(invetory, lang)

    if not pages:
        await bot.send_message(chatid, t('inventory.null', lang))
    
    else:
        await bot.set_state(userid, AlternativeStates.Inventory, chatid)
        async with bot.retrieve_data(userid, chatid) as data:
            data['pages'] = pages
            data['row'] = row
            data['items_data'] = items_data
            data['names'] = names
            data['page'] = 0
            data['filters'] = []

        await swipe_page(chatid, lang, 0, pages, row)

@bot.message_handler(state=AlternativeStates.Inventory, is_authorized=True)
async def inventory(message: Message):
    userid = message.from_user.id
    lang = message.from_user.language_code
    chatid = message.chat.id
    content = message.text

    async with bot.retrieve_data(userid, chatid) as data:
        pages = data['pages']
        row = data['row']
        items_data = data['items_data']
        names = data['names']
        page = data['page']

    if content == back_button:
        if page == 0: page = len(pages) - 1
        else: page -= 1

        await swipe_page(chatid, lang, page, pages, row)
        async with bot.retrieve_data(userid, chatid) as data: data['page'] = page
        
    elif content == forward_button:
        if page >= len(pages) - 1: page = 0
        else: page += 1

        await swipe_page(chatid, lang, page, pages, row)
        async with bot.retrieve_data(userid, chatid) as data: data['page'] = page
        
    else:
        print(content)