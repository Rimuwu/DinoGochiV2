from currency_converter import CurrencyConverter
from time import time
from bot.const import GAME_SETTINGS

main_currency = 'USD'
c = CurrencyConverter()

all_currency = [
    'EUR', 'BRL', 'TRY', 'PLN'
    ]
products = GAME_SETTINGS['products']

def convert(amout:int, from_currency:str='RUB', to_currency:str='USD') -> int:
    return round(c.convert(amout, from_currency, to_currency), 2)

def get_products():
    for product_key in products:
        product = products[product_key]

        for currency in all_currency:
            product['cost'][currency] = convert(
                product['cost'][main_currency], main_currency, currency)
    return products