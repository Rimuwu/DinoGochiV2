from PIL import Image, ImageDraw, ImageFilter, ImageFont
from random import choice 
from bot.config import conf
from bot.const import GAME_SETTINGS, DINOS

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
    id_l = []
    bg_p = Image.open(
        f"images/remain/backs/{choice(GAME_SETTINGS['egg_ask_backs'])}.png"
        )

    for i in range(3):
        rid = str(choice(list(DINOS['data']['egg'])))
        image = Image.open('images/' + str(DINOS['elements'][rid]['image']))
        bg_p = trans_paste(image, bg_p, 1.0, (i * 512, 0))

        id_l.append(rid)

    bg_p.save(f'{conf.temp_dir}/eggs.png')
    photo = open(f"{conf.temp_dir}/eggs.png", 'rb')

    return photo, id_l