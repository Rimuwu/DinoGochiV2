from bot.exec import bot

def dino_notification(dino_id, not_type: str):
    print(dino_id, not_type)

async def user_notification(user_id: int, not_type: str):
    print(user_id, not_type)
    await bot.send_message(user_id, not_type)