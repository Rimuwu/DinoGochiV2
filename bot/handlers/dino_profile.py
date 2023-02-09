from telebot import types

from bot.exec import bot
from bot.modules.data_format import chunks, list_to_keyboard, near_key
from bot.modules.dinosaur import Dino, Egg
from bot.modules.localization import t, get_data
from bot.modules.markup import markups_menu as m
from bot.modules.states import States
from bot.modules.user import User
from bot.modules.events import get_one_event


def dino_context(dino: Dino, lang: str) -> str:
    text = ''
    # text = t('p_profile.incubation_text', lang, time_end=)

    return text

def egg_context(egg: Egg, lang: str) -> str:
    text = t('p_profile.incubation_text', lang, time_end=egg.remaining_incubation_time())
    return text

async def send_m(userid, element, lang):
    text = ''
    img = element.image(lang)

    if type(element) == Dino:
        text = dino_context(element, lang)
    elif type(element) == Egg:
        text = egg_context(element, lang)
        
    await bot.send_photo(userid, img, text, reply_markup=m(userid, 'last_menu', language_code=lang))


@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def dino_profile(message: types.Message):
    user = User(message.from_user.id)
    lang = message.from_user.language_code
    elements = user.get_dinos() + user.get_eggs()

    if len(elements) == 0:
        await bot.send_message(user.userid, 
            t('p_profile.no_dinos_eggs'), lang)

    elif len(elements) == 1:
        element = elements[0]
        await send_m(user.userid, element, lang)

    else: # Несколько динозавров / яиц
        names, data_names = [], {}
        n, txt = 0, ''
        for element in elements:
            n += 1

            if type(element) == Dino:
                txt = f'{n}🦕 {element.name}'
            elif type(element) == Egg:
                txt = f'{n}🥚'
            
            data_names[txt] = element
            names.append(txt)
            
        buttons_list = list(chunks(names, 2))
        buttons_list.append([t('buttons_name.cancel', lang)])
        keyboard = list_to_keyboard(buttons_list, 2)

        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, States.choose_dino, message.chat.id)
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['dino_answer'] = data_names

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=keyboard)

@bot.message_handler(state=States.choose_dino, is_authorized=True)
async def answer_dino(message: types.Message):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data_names = data['dino_answer']

    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reset_data(message.from_user.id, message.chat.id)
    
    lang = message.from_user.language_code
    element = data_names[message.text]
    await send_m(message.from_user.id, element, lang)
