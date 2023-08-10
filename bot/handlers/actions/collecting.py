
from telebot.types import CallbackQuery, Message

from bot.config import mongo_client
from bot.const import GAME_SETTINGS
from bot.exec import bot
from bot.modules.data_format import list_to_inline, list_to_keyboard
from bot.modules.dinosaur import Dino, end_collecting
from bot.modules.images import dino_collecting
from bot.modules.inline import inline_menu
from bot.modules.item import counts_items
from bot.modules.localization import get_data, t, get_lang
from bot.modules.markup import count_markup
from bot.modules.markup import markups_menu as m
from bot.modules.states_tools import ChooseStepState
from bot.modules.user import User, count_inventory_items, premium
from bot.modules.quests import quest_process

users = mongo_client.bot.users
dinosaurs = mongo_client.bot.dinosaurs
collecting_task = mongo_client.tasks.collecting

async def collecting_adapter(return_data, transmitted_data):
    dino = transmitted_data['dino'] # type: Dino
    count = return_data['count']
    option = return_data['option']
    chatid = transmitted_data['chatid']
    userid = transmitted_data['userid']
    lang = transmitted_data['lang']
    
    eat_count = count_inventory_items(userid, ['eat'])
    st_premium = premium(userid)
    
    if st_premium and eat_count + count > GAME_SETTINGS['premium_max_eat_items'] \
        or not st_premium and \
        eat_count + count > GAME_SETTINGS['max_eat_items']:

        text = t(f'collecting.max_count', lang,
                eat_count=eat_count)
        await bot.send_message(chatid, text, reply_markup=m(
            userid, 'last_menu', lang))
    else:
        res_dino_status = dinosaurs.find_one({"_id": dino._id}, {'status': 1})
        if res_dino_status:
            if res_dino_status['status'] != 'pass':
                await bot.send_message(chatid, t('alredy_busy', lang), reply_markup=m(userid, 'last_menu', lang))
                return

            dino.collecting(userid, option, count)

            image = dino_collecting(dino.data_id, option)
            text = t(f'collecting.result.{option}', lang,
                    dino_name=dino.name, count=count)
            stop_button = t(f'collecting.stop_button.{option}', lang)
            markup = list_to_inline([
                {stop_button: f'collecting stop {dino.alt_id}'}])

            await bot.send_photo(chatid, image, text, reply_markup=markup)
            await bot.send_message(chatid, t('back_text.actions_menu', lang),
                                        reply_markup=m(userid, 'last_menu', lang)
                                        )


@bot.message_handler(text='commands_name.actions.collecting', 
                     dino_pass=True, nothing_state=True)
async def collecting_button(message: Message):
    userid = message.from_user.id
    chatid = message.chat.id

    user = User(userid)
    lang = user.lang
    last_dino = user.get_last_dino()

    if last_dino:
            if user.premium:
                max_count = GAME_SETTINGS['premium_max_collecting']
            else: max_count = GAME_SETTINGS['max_collecting']
            
            data_options = get_data('collecting.buttons', lang)
            options = dict(zip(data_options.values(), data_options.keys()))
            markup = list_to_keyboard([list(data_options.values()), 
                                    [t('buttons_name.cancel', lang)]], 2)
            
            steps = [
                {"type": 'option', "name": 'option', 
                 "data": {"options": options}, 
                 "translate_message": True,
                    'message': {'text': 'collecting.way', 
                    'reply_markup': markup}
                    },
                {"type": 'int', "name": 'count', 
                 "data": {"max_int": max_count}, 
                 "translate_message": True,
                    'message': {'text': 'collecting.wait_count', 
                    'reply_markup': count_markup(max_count, lang)}
                    }
                        ]
            await ChooseStepState(collecting_adapter, userid, chatid, 
                                        lang, steps, 
                                    transmitted_data={'dino': last_dino, 'delete_steps': True})
    
            
@bot.message_handler(text='commands_name.actions.progress')
async def collecting_progress(message: Message):
    userid = message.from_user.id
    chatid = message.chat.id

    user = User(userid)
    lang = user.lang
    last_dino = user.get_last_dino()
    if last_dino:
        
        data = collecting_task.find_one({'dino_id': last_dino._id})
        if data:
            stop_button = t(
                f'collecting.stop_button.{data["collecting_type"]}', lang)

            image = open(f'images/actions/collecting/{data["collecting_type"]}.png', 'rb')
            text = t(f'collecting.progress.{data["collecting_type"]}', lang,
                    now = data['now_count'], max_count=data['max_count']
                    )
            
            await bot.send_photo(chatid, image, text, 
                                 reply_markup=list_to_inline(
                                  [{stop_button: f'collecting stop {last_dino.alt_id}'}]
                                     ))
        else:
            await bot.send_message(chatid, '❌',
                                    reply_markup=m(userid, 'last_menu', lang)
                                    )
    

@bot.callback_query_handler(func=
                            lambda call: call.data.startswith('collecting'), is_authorized=True, private=True)
async def collecting_callback(callback: CallbackQuery):
    dino_data = callback.data.split()[2]
    action = callback.data.split()[1]

    lang = get_lang(callback.from_user.id)

    dino = Dino(dino_data) #type: ignore
    data = collecting_task.find_one({'dino_id': dino._id})
    if data and dino:
        items_list = []
        for key, count in data['items'].items():
            items_list += [key] * count

        items_names = counts_items(items_list, lang)

        if action == 'stop':
            await end_collecting(dino._id, 
                                 data['items'], data['sended'], 
                                 items_names)
            quest_process(data['sended'], data['collecting_type'], 
                          data['now_count'])