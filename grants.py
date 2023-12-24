from vk_api import image_handler
from PIL import (
    Image,
    ImageDraw,
    ImageFont
)


class GrantCreating:
    """инициализация"""
    def __init__(self, path):
        self.image = Image.open(path)
        self.artist = ImageDraw.Draw(self.image)
        self.font = "Star Platinum"

    """шрифтулькин"""
    def add_font(self, name_font, size):
        self.font = ImageFont.truetype(name_font, size)

    """вставка текста"""
    def add_text(self, coord, text, fill):
        self.artist.text(coord, text, fill, self.font)

    """VK-загрузчик"""
    def upload(self):
        self.image.save(image_handler, "PNG")
        self.image.close()

        # to be continued...
        image_handler.seek(0)
        return image_handler.getvalue()
  
