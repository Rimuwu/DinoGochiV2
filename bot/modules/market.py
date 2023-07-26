from time import time

from bson.objectid import ObjectId

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline, random_code, seconds_to_str
from bot.modules.item import counts_items, get_item_dict
from bot.modules.item import get_data as get_item_data
from bot.modules.localization import get_data, t
from bot.modules.user import get_inventory
from bot.const import ITEMS

products = mongo_client.market.products
sellers = mongo_client.market.sellers
puhs = mongo_client.market.puhs

async def add_product(owner_id: int, product_type: str, items, price, in_stock: int = 1,
                add_arg: dict = {}):
    """ Добавление продукта в базу данных

        product_type
            items_coins - продажа предметов за монеты
                items: list - продаваемые предметы
                price: int - цена

            coins_items - покупка предметов за монеты
                items: list - предметы которые требуется купить
                price: int - предлагаемая цена

            items_items - обмен предметов
                items: list - предметы на продаже
                price: list - требуемые предметы от покупателя

            auction - продажа предметов за монеты, но цена не фиксирована
                add_arg - {'end': время окончания аукциона, 'min_add': минимальная ставка}
                items: list - продаваемые предметы
                price: int - указывается стартовая цена, каждый покупатель выставляет цену больше
    """
    assert product_type in ['items_coins', 'coins_items', 'items_items', 'auction'], f'Тип ({product_type}) не совпадает c доступными'

    def generation_code(owner_id):
        code = f'{owner_id}_{random_code(8)}'
        if products.find_one({'alt_id': code}):
            code = generation_code(owner_id)
        return code

    data = {
        'add_time': int(time()),
        'type': product_type,
        'owner_id': owner_id,
        'alt_id': generation_code(owner_id),
        'items': items,
        'price': price,
        'in_stock': in_stock, # В запасе, сколько раз можно купить товар
        'bought': 0 # Уже кипили раз
    }

    if product_type == 'auction':
        data['end'] = add_arg['end']
        data['min_add'] = add_arg['min_add']
        data['users'] = []

    res = products.insert_one(data)
    await send_view_product(res.inserted_id, owner_id)

    return res.inserted_id

def create_seller(owner_id: int, name: str, description: str):
    """ Создание продавца / магазина
    """

    if not sellers.find_one({'owner_id': owner_id}):
        data = {
            'owner_id': owner_id,
            'earned': 0, # заработано монет
            'conducted': 0, # проведено сделок
            'name': name,
            'description': description,
            'auto_push': {
                'status': False,
                'lang': 'en',
                'channel': None
            }
        }

        sellers.insert_one(data)
        return True
    else: return False

def seller_ui(owner_id: int, lang: str, my_market: bool, name: str = ''):
    text, markup, img = '', None, None

    seller = sellers.find_one({'owner_id': owner_id})
    if seller:
        data = get_data('market_ui', lang)
        products_col = products.count_documents({'seller_id': seller['_id']})

        if my_market: owner = data['me_owner']
        else: owner = name

        status = ''
        if seller['earned'] <= 1000: status = 'needy'
        elif seller['earned'] <= 10000: status = 'stable'
        else: status = 'rich'

        text += f'{data["had"]} *{seller["name"]}*\n_{seller["description"]}_\n\n{data["owner"]} {owner}\n' \
                f'{data["earned"]} {seller["earned"]} {data[status]}\n{data["conducted"]} {seller["conducted"]}\n' \
                f'{data["products"]} {products_col}\n\n{data["my_option"]}'

        bt_data = {}
        if products_col:
            bt_data[data['buttons']['market_products']] = f"products {owner_id}"
        else: bt_data[data['buttons']['no_products']] = f" "

        markup = list_to_inline([bt_data])
        img = open(f'images/remain/market/{status}.png', 'rb')

    return text, markup, img

def generate_sell_pages(user_id: int, ignored_id: list = []):
    """ Получение инвентаря с исключением предметов, которые нельзя продать 
    """
    items, count = get_inventory(user_id, ignored_id)
    exclude = ignored_id
    for item in items:
        i = item['item']
        data = get_item_data(i['item_id'])

        if 'abilities' in i and 'interact' in i['abilities'] and not i['abilities']['interact']:
            exclude.append(i['item_id'])
            items.remove(item)
        elif 'cant_sell' in data and data['cant_sell']:
            exclude.append(i['item_id'])
            items.remove(item)
    return items, exclude

def product_ui(lang: str, product_id: ObjectId, i_owner: bool = False):
    """ Генерация сообщения для продукта
        i_owner: bool (option) - если true то добавляет кнопки изменения товара

    """
    text, coins_text, data_buttons = '', '', []

    product = products.find_one({'_id': product_id})
    if product:
        seller = sellers.find_one({'owner_id': product['owner_id']})
        if seller:
            product_type = product['type']
            items = product['items']
            price = product['price']
            
            items_id = []
            for i in items: items_id.append(i['item_id'])
            items_text = counts_items(items_id, lang)

            if product_type in ['items_coins', 'coins_items', 'auction']:
                # price: int
                coins_text = price

            elif product_type in ['items_items']:
                # price: list
                coins_text = counts_items(price, lang)

            text += t('product_ui.cap', lang) + '\n\n'
            text += t('product_ui.type', lang, type=t(f'product_ui.types.{product_type}', lang)) + '\n'
            text += t('product_ui.in_stock', lang, now=product['bought'], all=product['in_stock']) + '\n'

            if product_type != 'auction':
                text += t(f'product_ui.text.{product_type}', lang,
                        items=items_text, price=coins_text)
            else:
                end_time = seconds_to_str(product['end'] - int(time()))
                min_add = product['min_add']
                users = ''
                text += t(f'product_ui.text.{product_type}', lang,
                        items=items_text, price=coins_text, end_time=end_time, min_add=min_add, users=users)

            b_data = get_data(f'product_ui.buttons', lang)
            alt_id = product['alt_id']
            if i_owner:
                add_time = product['add_time']
                time_end = (add_time + 86_400 * 30) - int(time())

                text += f'\n\n' + t(f'product_ui.owner_message', lang, 
                                    time=seconds_to_str(time_end, lang, max_lvl='day'))

                data_buttons = [
                    {
                        b_data['edit_price']: f'product_info edit_price {alt_id}'
                    },
                    {
                        b_data['add']: f'product_info add {alt_id}',
                        b_data['delete']: f'product_info delete {alt_id}',
                        b_data['promotion']: f'product_info promotion {alt_id}'
                    }
                ]

            else:
                data_buttons = [
                    {
                        f"🔎 {seller['name']}": f"seller {seller['owner_id']}"
                    },
                    {
                        f"🔎 {seller['items_info']}": f"product_info items {seller['owner_id']}"
                    }
                ]
                if product_type == 'auction':
                    data_buttons[0][b_data['auction']] = f"product_info auction {alt_id}"
                else:
                    data_buttons[0][b_data['buy']] = f"product_info buy {alt_id}"

    buttons = list_to_inline(data_buttons)
    return text, buttons

async def send_view_product(product_id: ObjectId, owner_id: int):
    res = puhs.find_one({'owner_id': owner_id})
    product = products.find_one({'_id': product_id})

    if res and product:
        channel = res['channel_id']
        lang = res['lang']

        text, markup = product_ui(lang, product_id, False)

        buttons = [
            {
                t('product_ui.buttons.view', lang): f"product_info view {product['alt_id']}"
            }
        ]

        markup = list_to_inline(buttons)
        await bot.send_message(channel, text, reply_markup=markup, parse_mode='Markdown')

def create_push(owner_id: int, channel_id: int, lang: str):

    data = {
        'owner_id': owner_id,
        'channel_id': channel_id,
        'lang': lang
    }

    puhs.insert_one(data)

def generate_items_pages(ignored_id: list = []):
    """ Получение страниц со всеми предметами
    """
    items = []
    exclude = ignored_id
    for key, item in ITEMS.items():
        data = get_item_dict(key)
        if 'cant_sell' in item and item['cant_sell']:
            exclude.append(key)
        else: items.append({'item': data, 'count': 1})
    return items, exclude