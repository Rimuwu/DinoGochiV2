import io
from random import choice, randint

import requests
from PIL import Image, ImageDraw, ImageFont
from telebot.util import pil_image_to_file

from bot.const import DINOS, GAME_SETTINGS
from bot.modules.data_format import seconds_to_str
from bot.modules.localization import get_data


def trans_paste(fg_img, bg_img, alpha=10.0, box=(0, 0)):
    """Накладывает одно изображение на другое.
    """
    fg_img_trans = Image.new('RGBA', fg_img.size)
    fg_img_trans = Image.blend(fg_img_trans, fg_img, alpha)
    bg_img.paste(fg_img_trans, box, fg_img_trans)

    return bg_img

def create_eggs_image():
    """Создаёт изображение выбора яиц.
    """
    id_l = [] #Хранит id яиц
    bg_p = Image.open(
        f'images/remain/backs/{choice(GAME_SETTINGS["egg_ask_backs"])}.png'
        ) #Случайный фон

    for i in range(3):
        rid = str(choice(list(DINOS['data']['egg']))) #Выбираем рандомное яйцо
        image = Image.open('images/' + str(DINOS['elements'][rid]['image']))
        bg_p = trans_paste(image, bg_p, 1.0, (i * 512, 0)) #Накладываем изображение
        id_l.append(rid)

    return pil_image_to_file(bg_p), id_l

def create_egg_image(egg_id: int, rare: str='random', seconds: int=0, lang: str='en'):
    """Создаёт изобраение инкубации яйца
       Args:
       egg_id - id яйца
       rare - редкость (от этого зависит цвет надписи)
       seconds - секунды до конца инкубации
       lang - язык текста
    """
    img_dates = {
        'random': (207, 70, 204),
        'com': (108, 139, 150),
        'unc': (68, 235, 90),
        'rar': (68, 143, 235),
        'myt': (230, 103, 175),
        'leg': (255, 212, 59)
    }

    rares = get_data('rare', lang)
    time_end = seconds_to_str(seconds, lang, mini=True)
    text_dict = get_data('p_profile', lang)

    quality_text = rares[rare][1]
    fill = img_dates[rare]

    bg_p = Image.open(f'images/remain/egg_profile.png')
    egg = Image.open(f'images/{DINOS["elements"][str(egg_id)]["image"]}')
    egg = egg.resize((290, 290), Image.Resampling.LANCZOS)
    img = trans_paste(egg, bg_p, 1.0, (-50, 40))

    idraw = ImageDraw.Draw(img)
    line1 = ImageFont.truetype('fonts/Comic Sans MS.ttf', size=35)
    line2 = ImageFont.truetype('fonts/Comic Sans MS.ttf', size=45)
    line3 = ImageFont.truetype('fonts/Comic Sans MS.ttf', size=55)

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
    return pil_image_to_file(img)

def create_dino_image(dino_id: int, stats: dict, quality: str='com', profile_view: int=1, age: int = 30, custom_url: str=''):
    """Создание изображения динозавра
       Args:
       dino_id - id картинки динозавра
       stats - словарь с харрактеристиками динозавра ( {'heal': 0, 'eat': 0, 'sleep': 0, 'game': 0, 'mood': 0} )
    """
    if age > 30: age = 30
    def formul(age: int, max_size, max_x, max_y, days = 30):
        f = age * ((max_size-150) // days) + 150
        x = int(age * ((max_x) / days))
        y = int(age * ((max_y-150) / days)+150)
        return f, x, y

    def formul2(age: int, max_size, max_x, max_y, days = 30):
        f = age * ((max_size-150) // days) + 150
        x = int(age * ((max_x-250) / days)+250)
        y = int(age * ((max_y-100) / days)+100)
        return f, x, y

    dino_data = DINOS['elements'][str(dino_id)]
    img = Image.open(
            f'images/remain/backgrounds/{dino_data["class"].lower()}.png')
    if custom_url:
        try:
            response = requests.get(custom_url, stream = True)
            response = Image.open(io.BytesIO(response.content))
            response = response.convert("RGBA")
            img = response.resize((900, 350), Image.Resampling.LANCZOS)
        except: custom_url = ''
        
    if profile_view != 4:
        panel_i = Image.open(
            f'images/remain/panels/v{profile_view}_{quality}.png')
        img = trans_paste(panel_i, img, 1.0)

    dino_image = Image.open(f'images/{dino_data["image"]}')
    dino_image = dino_image.resize((1024, 1024), Image.Resampling.LANCZOS)

    heal, eat, energy = stats['heal'], stats['eat'], stats['energy']
    game, mood = stats['game'], stats['mood']
    sz, x, y = 450, 0, 0

    idraw = ImageDraw.Draw(img)

    if profile_view == 1:
        line1 = ImageFont.truetype('fonts/Aqum.otf', size=30)
        sz, x, y = formul(age, 400, 75, -60)

        idraw.text((518, 93), f'{heal}%', font = line1)
        idraw.text((518, 170), f'{eat}%', font = line1)

        idraw.text((718, 93), f'{game}%', font = line1)
        idraw.text((718, 170), f'{mood}%', font = line1)
        idraw.text((718, 247), f'{energy}%', font = line1)

    elif profile_view == 2:
        line1 = ImageFont.truetype('fonts/Aqum.otf', size=25)
        sz, x, y = formul2(age, 450, 385, -180)
        text_y = 280

        idraw.text((157, text_y), f'{heal}%', font = line1)
        idraw.text((298, text_y), f'{eat}%', font = line1)
        idraw.text((440, text_y), f'{energy}%', font = line1)

        idraw.text((585, text_y), f'{game}%', font = line1)
        idraw.text((730, text_y), f'{mood}%', font = line1)

    elif profile_view == 3:
        line1 = ImageFont.truetype('fonts/Aqum.otf', size=25)
        sz, x, y = formul2(age, 450, 275, -80)
        text_y = 50

        idraw.text((157, text_y), f'{heal}%', font = line1)
        idraw.text((298, text_y), f'{eat}%', font = line1)
        idraw.text((440, text_y), f'{energy}%', font = line1)

        idraw.text((585, text_y), f'{game}%', font = line1)
        idraw.text((730, text_y), f'{mood}%', font = line1)
    
    elif profile_view == 4:
        sz, x, y = formul2(age, 450, randint(170, 550), randint(-180, -100))
        if randint(0, 1):
            dino_image = dino_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    
    # Рисует квадрат границы динозавра
    # idraw.rectangle((y + x, y, sz + y + x, sz + y), outline=(255, 0, 0))
    
    dino_image = dino_image.resize((sz, sz), Image.Resampling.LANCZOS)
    img = trans_paste(dino_image, img, 1.0, (y + x, y, sz + y + x, sz + y))

    return pil_image_to_file(img)
