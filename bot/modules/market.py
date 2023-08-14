from time import time

from bson.objectid import ObjectId

from bot.config import mongo_client
from bot.exec import bot
from bot.modules.data_format import list_to_inline, random_code, seconds_to_str
from bot.modules.item import counts_items, get_item_dict, AddItemToUser, CheckCountItemFromUser, RemoveItemFromUser
from bot.modules.item import get_data as get_item_data
from bot.modules.images import market_image
from bot.modules.localization import get_data, t, get_lang
from bot.modules.user import get_inventory, take_coins, premium
from bot.const import ITEMS
from bot.modules.localization import t
from bot.modules.notifications import user_notification

products = mongo_client.market.products
sellers = mongo_client.market.sellers
puhs = mongo_client.market.puhs
preferential = mongo_client.market.preferential

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
        data['end'] = add_arg['end'] + int(time())
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
            'custom_image': '',
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
        products_col = products.count_documents({'owner_id': owner_id})

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
        d_but = data['buttons']
        if not my_market:
            if products_col:
                bt_data[d_but['market_products']] = f"seller all {owner_id}"
            else: bt_data[d_but['no_products']] = f" "
            bt_data[d_but['сomplain']] = f'seller сomplain {owner_id}'
        else:
            bt_data.update(
                {
                d_but['edit_text']: f'seller edit_text {owner_id}',
                d_but['edit_name']: f'seller edit_name {owner_id}',
                d_but['edit_image']: f'seller edit_image {owner_id}',
                }
            )

            if products_col >= 2:
                bt_data[d_but['cancel_all']] = f'seller cancel_all {owner_id}'

        markup = list_to_inline([bt_data])
        if 'custom_image' in seller and seller['custom_image'] and premium(owner_id):
            img = market_image(seller['custom_image'], status)
        else:
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
                items_price = []
                for i in price: items_price.append(i['item_id'])
                coins_text = counts_items(items_price, lang)

            text += t('product_ui.cap', lang) + '\n\n'
            text += t('product_ui.type', lang, type=t(f'product_ui.types.{product_type}', lang)) + '\n'
            text += t('product_ui.in_stock', lang, now=product['bought'], all=product['in_stock']) + '\n\n'

            if product_type != 'auction':
                text += t(f'product_ui.text.{product_type}', lang,
                        items=items_text, price=coins_text)
            else:
                end_time = seconds_to_str(product['end'] - int(time()), lang, max_lvl='hour')
                min_add = product['min_add']
                users, a = '', 1

                if product['users']:
                    for i in product['users']:
                        users += f'{a} {i["name"]} {i["coins"]}'
                        a += 1
                else: users = t('product_ui.no_action_users', lang)

                text += t(f'product_ui.text.{product_type}', lang,
                        items=items_text, price=coins_text, end_time=end_time, min_add=min_add, users=users)

            b_data = get_data(f'product_ui.buttons', lang)
            alt_id = product['alt_id']
            if i_owner:
                add_time = product['add_time']
                time_end = (add_time + 86_400 * 31) - int(time())
                
                if product_type in ['auction', 'items_coins']:
                    text += f'\n\n' + t(f'product_ui.owner_message', lang, 
                                        time=seconds_to_str(time_end, lang, max_lvl='day'))

                data_buttons = [
                    {},
                    {
                        b_data['delete']: f'product_info delete {alt_id}'
                    }
                ]
                if is_promotion(product['_id']):
                    data_buttons[1][b_data['promotion']] = f'product_info promotion {alt_id}'
                else:
                    data_buttons[1][b_data['alredy_promotion']] = f' '

                if product_type != 'auction':
                    data_buttons[0][b_data['add']] = f'product_info add {alt_id}'

                if product_type in ['items_coins', 'coins_items']:
                    data_buttons[0][b_data['edit_price']] = f'product_info edit_price {alt_id}'

            else:
                data_buttons = [
                    {
                        f"🔎 {seller['name']}": f"seller info {seller['owner_id']}"
                    },
                    {
                        f"{b_data['items_info']}": f"product_info items {alt_id}"
                    }
                ]
                if product_type == 'auction':
                    data_buttons[0][b_data['auction']] = f"product_info buy {alt_id}"
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

async def delete_product(baseid = None, alt_id = None):
    if baseid:
        product = products.find_one({'_id': baseid})
    else:
        product = products.find_one({'alt_id': alt_id})

    if product:
        p = product
        ptype = p['type']
        remained = p['in_stock'] - p['bought'] # Осталось / в запасе
        owner = p['owner_id']

        if ptype in ['items_coins', 'items_items', 'auction']: 
            for item in p['items']:
                if 'abillities' in item: abil = item['abillities']
                else: abil = {}
                if remained:
                    AddItemToUser(owner, item['item_id'], remained, abil)

        elif ptype == 'coins_items':
            coins = p['price'] * remained
            if coins: take_coins(owner, coins, True)

        if ptype == 'auction':
            for user in product['users']:
                if user['status'] == 'win':
                    # Выдача предметов победителю
                    for item in p['items']:
                        if 'abillities' in item: abil = item['abillities']
                        else: abil = {}
                        if remained:
                            AddItemToUser(owner, item['item_id'], remained, abil)

                    # Выдача монет создателю аукциона
                    two_percent = (product['price'] // 100) * 2
                    take_coins(owner, user['coins'], True)

                    # Сообщение
                    id_list = []
                    for i in product['items']: id_list.append(i['item_id'])
                    c_items = counts_items(id_list, user['lang'])
                    text = t('auction.delete_auction', user['lang'], items=c_items)

                else:
                    # Не победитель
                    take_coins(user['userid'], user['coins'], True)

                    # Сообщение
                    id_list = []
                    for i in product['items']: id_list.append(i['item_id'])
                    c_items = counts_items(id_list, user['lang'])
                    text = t('auction.delete_auction', user['lang'], items=c_items)

                try:
                    await bot.send_message(user['userid'], text)
                except: pass

        # Уведомление о удаление товара
        owner_lang = get_lang(owner)
        preview = preview_product(
            product['items'], product['price'], product['type'], owner_lang)
        await user_notification(owner, 'product_delete', owner_lang,
                                preview=preview)

        products.delete_one({'_id': product['_id']})
        return True
    else: return False

def new_participant(baseid: ObjectId, userid: int, coins: int, name: str, lang: str):
    """ Добавляет нового участника аукциона к продукту
    """
    product = products.find_one({'_id': baseid})
    if product:
        if product['type'] == 'auction':
            data = {
                'userid': userid,
                'name': name,
                'lang': lang,
                'coins': coins,
                'status': 'member'
            }
            products.update_one({'_id': baseid}, {'$push': {'users': data}})
            return True
    return False

def preview_product(items: list, price, ptype: str, lang: str):
    """ Создаёт превью продукта 
        Пример:
            Курица х1, Банан х3 = 300 монет
            Курица х1, Банан х3 = 300 монет (⌛) # Аукцион
    """
    text = ''

    id_list = []
    for i in items: id_list.append(i['item_id'])
    items_text = counts_items(id_list, lang)

    if type(price) == int: price_text = f'{price} 🪙'
    else: 
        id_list = []
        for i in price: id_list.append(i['item_id'])
        price_text = counts_items(id_list, lang) # list

    if ptype != 'coins_items':
        text = f'{items_text} = {price_text}'
    else: text = f'{price_text} = {items_text}'
    if ptype == 'auction': text += ' (⌛)'

    return text

async def buy_product(pro_id: ObjectId, col: int, userid: int, name: str, lang: str=''):
    """ Покупка продукта / участние в аукционе
    """
    product = products.find_one({'_id': pro_id})
    if product:
        p_tp = product['type']
        owner = product['owner_id']

        if col > product['in_stock'] - product['bought']:
            return False, 'erro_max_col'
        else:
            if p_tp == 'items_coins':
                col_price = col * product['price']
                two_percent = (col_price // 100) * 2

                status = take_coins(userid, -col_price, True)

                if status:
                    for item in product['items']:
                        item_id = item['item_id']
                        if 'abillities' in item: abil = item['abillities']
                        else: abil = {}
                        AddItemToUser(userid, item_id, col, abil)

                    # Выдача монет владельцу
                    take_coins(owner, col_price - two_percent, True)

                else: return False, 'error_no_coins'

            elif p_tp == 'coins_items':
                items_status, n = [], 0
                col_price = col * product['price']

                for item in product['items']:
                    item_id = item['item_id']
                    if 'abillities' in item: abil = item['abillities']
                    else: abil = {}

                    status = CheckCountItemFromUser(userid, col, item_id, abil)
                    items_status.append(status)
                    n += 1

                take_coins(userid, col_price, True)

                if not all(items_status):
                    return False, 'error_no_items'
                else:
                    for item in product['items']:
                        item_id = item['item_id']
                        if 'abillities' in item: abil = item['abillities']
                        else: abil = {}
                        RemoveItemFromUser(userid, item_id, col, abil)

                    take_coins(userid, (col * product['price']), True)

            elif p_tp == 'item_items':
                items_status, n = [], 0
                for item in product['price']:
                    item_id = item['item_id']
                    if 'abillities' in item: abil = item['abillities']
                    else: abil = {}

                    status = CheckCountItemFromUser(userid, col, item_id, abil)
                    items_status.append(status)
                    n += 1

                if not all(items_status):
                    return False, 'error_no_items'
                else: 
                    for item in product['price']:
                        item_id = item['item_id']
                        if 'abillities' in item: abil = item['abillities']
                        else: abil = {}
                        RemoveItemFromUser(userid, item_id, col, abil)

                    for item in product['items']:
                        item_id = item['item_id']
                        if 'abillities' in item: abil = item['abillities']
                        else: abil = {}
                        AddItemToUser(userid, item_id, col, abil)

            elif p_tp == 'auction':
                # col - ставка пользователя

                status = take_coins(userid, -col, True)
                if status:
                    new_participant(pro_id, userid, col, name, lang)
                else: return False, 'error_no_coins'

            if p_tp != 'auction':
                sellers.update_one({'owner_id': userid}, {"$inc": {
                    'earned': col * product['price'],
                    'conducted': col
                }})

                if product['bought'] + col >= product['in_stock']:
                    await delete_product(pro_id)
                else:
                    products.update_one({'_id': pro_id}, {'$inc': {'bought': col}})

            # Уведомление о покупке
            owner_lang = get_lang(owner)
            preview = preview_product(
                product['items'], product['price'], product['type'], owner_lang)
            await user_notification(owner, 'product_buy', owner_lang,
                                    preview=preview, col=col, price=col * product['price'], name=name, alt_id=product['alt_id'])
            return True, 'ok'

    return False, 'erro_no_product'

def create_preferential(product_id: ObjectId, seconds: int, owner_id: int):

    data = {
        'product_id': product_id,
        'end': seconds + int(time()),
        'owner_id': owner_id
    }

    preferential.insert_one(data)

def check_preferential(owner_id: int, product_id: ObjectId):
    """ Проверка на максимальное количество продвигаемых продуктов, а так же добавлен ли он в продвижение
    """
    col = preferential.count_documents({'owner_id': owner_id})
    perf = preferential.count_documents({'product_id': product_id})
    premium_st = premium(owner_id)

    if premium_st: un = 10
    else: un = 5

    if col >= un: return False, 1
    if perf > 0: return False, 2
    return True, 0

def is_promotion(product_id: ObjectId):
    col = preferential.count_documents({'product_id': product_id})
    return col