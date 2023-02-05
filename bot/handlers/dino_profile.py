from telebot import types
from telebot.asyncio_handler_backends import State, StatesGroup

from bot.exec import bot
from bot.modules.localization import t
from bot.modules.user import User

from bot.modules.dinosaur import Dino, Egg
from bot.modules.data_format import list_to_keyboard, chunks


class States(StatesGroup):
    profile = State()


def dino_context(element: Dino, lang: str) -> str:
    text = ''
    
    return text

def egg_context(element: Egg, lang: str) -> str:
    text = ''
    
    return text


@bot.message_handler(text='commands_name.dino_profile', is_authorized=True)
async def dino_profile(message: types.Message):
    user = User(message.from_user.id)
    lang = message.from_user.language_code
    elements = user.get_dinos() + user.get_eggs()

    if len(elements) == 0:
        await bot.send_message(user.userid, 
            t('p_profile.no_dinos_eggs'), lang)

    elif len(elements) == 1:
        text = ''
        element = elements[0]
        img = element.image(lang)

        if type(element) == Dino:
            text = dino_context(element, lang)
        elif type(element) == Egg:
            text = egg_context(element, lang)
            
        await bot.send_photo(message.from_user.id, img, text)

    else: # Несколько динозавров / яиц
        
        names = []
        data_names = {} 
        n = 0

        for element in elements:
            n += 1
            txt = ''

            if type(element) == Dino:
                txt = f'{n}# 🦕 {element.name}'
                
            elif type(element) == Egg:
                txt = f'{n}# 🥚'
            
            data_names[txt] = element
            names.append(txt)
            
        buttons_list = list(chunks(names, 2))
        buttons_list.append([t('buttons_name.cancel', lang)])
        keyboard = list_to_keyboard(buttons_list, 2)

        # Устанавливаем состояния и передаём данные
        await bot.set_state(user.userid, States.profile, message.chat.id)
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['dino_answer'] = data_names

        await bot.send_message(user.userid, t('p_profile.choose_dino', lang), reply_markup=keyboard)
    # else:
    #     eggs = user.get_eggs()
    #     if len(eggs) != 0:
    #         egg = eggs[0]
    #         print(egg.__dict__)
    #         img = egg.image(message.from_user.language_code)

    #         await bot.send_photo(message.from_user.id, img)

@bot.message_handler(state=States.profile, is_authorized=True)
async def answer_dino(message: types.Message):
    print(message.text)

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data_names  = data['dino_answer']
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reset_data(message.from_user.id, message.chat.id)
    
    print(data_names)
