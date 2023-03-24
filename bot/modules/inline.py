from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.modules.item import counts_items
from bot.modules.item import get_data as get_item_data
from bot.modules.item import get_item_dict, get_name, item_code
from bot.modules.localization import get_data as get_loc_data
from bot.modules.localization import t
from bot.modules.logs import log


def inline_menu(markup_key: str = 'delete_message', lang: str = 'en', **kwargs):
    markup_inline = InlineKeyboardMarkup()
    text, callback = '-', '-'
    standart_keys = [
        'delete_message', 'send_request',
        'requests', 'dino_profile'
    ]

    if markup_key in standart_keys:
        text = t(f'inline_menu.{markup_key}.text', lang, **kwargs)
        callback = t(f'inline_menu.{markup_key}.callback', lang, **kwargs)

    else:
        log(prefix='InlineMarkup', 
            message=f'not_found_key Data: {markup_key}', lvl=2)
    
    markup_inline.add(
        InlineKeyboardButton(text=text, callback_data=callback))
    return markup_inline

def item_info_markup(item: dict, lang):
    markup_inline = InlineKeyboardMarkup()
    item_data = get_item_data(item['item_id'])
    loc_data = get_loc_data('item_info.static.buttons', lang)
    
    markup_inline.add(
        InlineKeyboardButton(text=loc_data['use'], 
                        callback_data=f"item use {item_code(item)}"),
        InlineKeyboardButton(text=loc_data['delete'],
                        callback_data=f"item delete {item_code(item)}")
    )
    markup_inline.add(InlineKeyboardButton(text=loc_data['exchange'],
                        callback_data=f"item exchange {item_code(item)}"))

    if item_data['type'] == 'recipe':
        for item_cr in item_data["create"]:
            data = get_item_dict(item_cr['item'])
            name = loc_data['created_item'].format(
                        item=get_name(item_cr['item'], lang))

            markup_inline.add(InlineKeyboardButton(text=name,
                        callback_data=f"item info {item_code(data)}"))

    if "ns_craft" in item_data:
        for cr_dct_id in item_data["ns_craft"].keys():
            bt_text = ''
            cr_dct = item_data["ns_craft"][cr_dct_id]

            bt_text += counts_items(cr_dct["materials"], lang)
            bt_text += ' = '
            bt_text += counts_items(cr_dct["create"], lang)
            
            markup_inline.add(InlineKeyboardButton(text=bt_text,
                            callback_data=f"ns_craft {item_code(item)} {cr_dct_id} {cr_dct_id}"))
    
    return markup_inline