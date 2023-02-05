from PIL import Image, ImageDraw, ImageFilter, ImageFont
from random import choice 
from bot.const import GAME_SETTINGS, DINOS
from bot.modules.localization import get_data
from bot.modules.data_format import seconds_to_str
from bot.const import DINOS

def trans_paste(fg_img, bg_img, alpha=10.0, box=(0, 0)):
    """Накладывает одно изображение на другое.
    """
    fg_img_trans = Image.new("RGBA", fg_img.size)
    fg_img_trans = Image.blend(fg_img_trans, fg_img, alpha)
    bg_img.paste(fg_img_trans, box, fg_img_trans)

    return bg_img

def create_eggs_image():
    """Создаёт изображение выбора яиц.
    """
    id_l = [] #Хранит id яиц
    bg_p = Image.open(
        f"images/remain/backs/{choice(GAME_SETTINGS['egg_ask_backs'])}.png"
        ) #Случайный фон

    for i in range(3):
        rid = str(choice(list(DINOS['data']['egg']))) #Выбираем рандомное яйцо
        image = Image.open('images/' + str(DINOS['elements'][rid]['image']))
        bg_p = trans_paste(image, bg_p, 1.0, (i * 512, 0)) #Накладываем изображение
        id_l.append(rid)

    return bg_p, id_l

def create_egg_image(egg_id: int, rare: str='random', seconds: int=0, lang: str='en'):
    """Создаёт изобраение инкубации яйца
    """
    img_dates = {
        'random': (207, 70, 204),
        'com': (108, 139, 150),
        'unc': (68, 235, 90),
        'rar': (68, 143, 235),
        'myt': (230, 103, 175),
        'leg': (255, 212, 59)
    }

    rares = get_data('rare', lang) #type: dict
    time_end = seconds_to_str(seconds, lang, mini=True)
    text_dict = get_data('p_profile', lang) #type: dict

    quality_text = rares[rare][1]
    fill = img_dates[rare]

    bg_p = Image.open(f"images/remain/egg_profile.png")
    egg = Image.open(f"images/{DINOS['elements'][str(egg_id)]['image']}")
    egg = egg.resize((290, 290), Image.Resampling.LANCZOS)
    img = trans_paste(egg, bg_p, 1.0, (-50, 40))

    idraw = ImageDraw.Draw(img)
    line1 = ImageFont.truetype("fonts/Comic Sans MS.ttf", size=35)
    line2 = ImageFont.truetype("fonts/Comic Sans MS.ttf", size=45)
    line3 = ImageFont.truetype("fonts/Comic Sans MS.ttf", size=55)

    idraw.text((310, 110), text_dict['text_info'], 
            font=line3,
            stroke_width=1
    )
    idraw.text((210, 210), text_dict['text_ost'], 
            font=line2
    )
    idraw.text(text_dict['time_position'], time_end, 
            font=line1, 
    )
    idraw.text((210, 270), text_dict['rare_name'],
            font=line2
    )
    idraw.text(text_dict['rare_position'], quality_text, 
            font=line1, 
            fill=fill
    )
    return img

