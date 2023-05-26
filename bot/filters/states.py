from telebot.asyncio_filters import AdvancedCustomFilter
from telebot.types import Message, CallbackQuery

from bot.exec import bot

class NothingState(AdvancedCustomFilter):
    key = 'nothing_state'

    async def check(self, call: CallbackQuery, status: bool):
        state = await bot.get_state(call.from_user.id, call.message.chat.id)

        if not state and status: return True
        elif not state and not status: return False

        elif state and status: return False
        elif state and not status: return True

bot.add_custom_filter(NothingState())