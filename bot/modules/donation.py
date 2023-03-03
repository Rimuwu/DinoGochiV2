import aiohttp
from bot.config import conf

headers = {
    'Authorization': 'Bearer {token}'.format(token=conf.donation_token),
}

async def get_donations() -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.donationalerts.com/api/v1/alerts/donations', headers=headers) as response:
            data = dict(await response.json())
            return data['data']