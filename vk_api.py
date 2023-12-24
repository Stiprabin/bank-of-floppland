from config import CONFIG
from io import BytesIO
from vkbottle.bot import BotLabeler
from vkbottle.callback import BotCallback
from vkbottle import (
    API,
    CtxStorage,
    PhotoMessageUploader,
    BuiltinStateDispenser
)


# инициализация объектов VK API
api = API(CONFIG['TOKEN'])
labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()
ctx = CtxStorage()
uploader = PhotoMessageUploader(api)

callback = BotCallback(url=CONFIG['URL'],
                       title=CONFIG['TITLE'],
                       secret_key=CONFIG['SECRET_KEY'])


# не совсем VK API... но пусть будет тут
image_handler = BytesIO()
    
