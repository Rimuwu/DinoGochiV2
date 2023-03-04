import json
import os
from time import time

import aiohttp

from bot.config import conf, mongo_client
from bot.exec import bot
from bot.modules.currency import get_products
from bot.modules.logs import log
from bot.modules.notifications import user_notification

users = mongo_client.bot.users

directory = 'bot/data/donations.json'
processed_donations = {}
headers = {
    'Authorization': 'Bearer {token}'.format(token=conf.donation_token),
}

def save(data):
    """Сохраняет данные в json
    """
    with open(directory, 'w') as file:
        json.dump(data, file, sort_keys=True, indent=4)

def OpenDonatData() -> dict:
    """Загружает данные обработанных донатов
    """
    processed_donations = {}
    try:
        with open(directory, encoding='utf-8') as f: 
            processed_donations = json.load(f)
    except Exception as error:
        if not os.path.exists(directory):
            with open(directory, 'w') as f:
                f.write('{}')
        else:
            log(prefix='OpenDonatData', message=f'Error: {error}', lvl=4)
    return processed_donations

async def get_donations() -> list:
    """Получает донаты
    """
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.donationalerts.com/api/v1/alerts/donations', headers=headers) as response:
            data = dict(await response.json())
            return data['data']

def save_donation(userid, amount, status, product, 
            issued_reward, time_data):
    """
    id: {
        'userid': int, 
        'amount': int,
        'status': str,
        'product': str | None,
        'issued_reward': bool,
        'time': int
    }
    """
    data = {
        'userid': userid, 
        'amount': amount,
        'status': status,
        'product': product,
        'issued_reward': issued_reward,
        'time': time_data
    }
    return data

async def send_donat_notification(userid:int, message_key:str, **kwargs):
    try:
        chat_user = await bot.get_chat_member(userid, userid)
        user = chat_user.user
        lang = user.language_code
    except Exception as e:
        log(prefix='send_donat_notification', message=f'Error {e}', lvl=3)
        lang = 'en'

    await user_notification(userid, f'donation', lang, add_way=message_key, **kwargs)

async def give_reward(userid:int, product_key:str):
    products = get_products()
    product = products['product_key']
    
    if product['type'] == 'kit':
        ...
    elif product['type'] == 'subscription':
        ...

    await send_donat_notification(userid, 'reward')

async def check_donations():
    processed_donations = OpenDonatData()
    all_donations = await get_donations()
    products = get_products()
    delete_doc = []

    for donat in all_donations:
        donation_data = {}
        if str(donat['id']) not in processed_donations.keys():
            #Донат не был ранее обработан
            if int(time()) - donat['created_at_ts'] <= 3024000:
                if donat['username'].isdigit():
                    userid = int(donat['username'])
                    user = users.find_one({'userid': userid})
                    if user:
                        product_key = donat['message'].split('#$#')[0]
                        if product_key in products:
                            product = products[product_key]

                            if donat['currency'] in product['cost']:
                                cost = product['cost'][donat['currency']]
                                rub_cost = product['cost']['RUB']

                                if donat['amount'] >= cost:
                                    await give_reward(userid, product_key)

                                    donation_data = save_donation(
                                        donat['username'], 
                                        donat['amount'], 'done', 
                                        product_key, True, donat['created_at_ts']
                                    )

                                elif donat['amount_in_user_currency'] >= rub_cost:
                                    await give_reward(userid, product_key)

                                    donation_data = save_donation(
                                        donat['username'], 
                                        donat['amount'], 'done', 
                                        product_key, True, donat['created_at_ts']
                                    )

                                else:
                                    #Сумма доната меньше, чем стоимость продукта
                                    error = 'amount_error'
                                    donation_data = save_donation(
                                        donat['username'], 
                                        donat['amount'], error, 
                                        product_key, False, donat['created_at_ts']
                                    )

                                    donation_data['difference'] = [
                                        cost - donat['amount'], 
                                        rub_cost - donat['amount_in_user_currency']
                                        ]
                                    
                                    await send_donat_notification(userid, error, 
                                                                difference=donation_data['difference'][0],
                                                                currency=donat['currency']
                                                                )
                            else:
                                #Валюта доната не найдена в возможных
                                error = 'currency_key_error'
                                donation_data = save_donation(donat['username'], 
                                    donat['amount'], error, 
                                    product_key, False, donat['created_at_ts']
                                    )
                                donation_data['error_key'] = donat['currency']
                                await send_donat_notification(userid, error, 
                                                            currency_key=donat['currency'])
                        else:
                            #неправильно указан ключ товара
                            error = 'product_key_error'
                            donation_data = save_donation(donat['username'], 
                                donat['amount'], error, None, False, donat['created_at_ts']
                                )
                            donation_data['error_key'] = product_key[:12]
                            await send_donat_notification(userid, error, 
                                                        product_key=product_key[:12])

                    else:
                        #id юзера не найдено в базе
                        error = 'userid_not_in_base'
                        donation_data = save_donation(donat['username'], 
                            donat['amount'], error, None, False, donat['created_at_ts']
                            )
                else:
                    #id юзера может быть только число
                    error = 'userid_error'
                    donation_data = save_donation(donat['username'], 
                            donat['amount'], error, None, False, donat['created_at_ts']
                            )
        else:
            if int(time()) - donat['created_at_ts'] >= 3024001:
                del processed_donations[str(donat['id'])]

        processed_donations[str(donat['id'])] = donation_data
    save(processed_donations)





