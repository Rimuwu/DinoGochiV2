from bot.exec import bot
from bot.modules.user import get_frineds, user_name, user_info
from bot.modules.states_tools import ChoosePagesState


async def friend_handler(friend, transmitted_data):
    lang = transmitted_data['lang']
    chatid = transmitted_data['chatid']

    text = user_info(friend, lang)

    photos = await bot.get_user_profile_photos(friend.id, limit=1)
    if photos.photos:
        photo_id = photos.photos[0][0].file_id #type: ignore
        await bot.send_photo(chatid, photo_id, text, parse_mode='Markdown')
    else:
        await bot.send_message(chatid, text, parse_mode='Markdown')

async def start_friend_menu(function, 
                userid: int, chatid: int, lang: str, 
                one_element: bool=False,
                transmitted_data = None):
    friends = get_frineds(userid)['friends']
    options = {}
    
    if function == None: function = friend_handler
    
    for friend_id in friends:
        try:
            chat_user = await bot.get_chat_member(friend_id, friend_id)
            friend = chat_user.user
        except: friend = None
        if friend: options[user_name(friend)] = friend
    
    await ChoosePagesState(
        function, userid, chatid, lang, options, 
        horizontal=2, vertical=3,
        autoanswer=False, one_element=one_element,  
        transmitted_data=transmitted_data)