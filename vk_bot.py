from loguru import logger
from vkbottle import Bot
from vk_api import (
    api,
    labeler,
    callback,
    state_dispenser
)
from handlers import (
    main_text,
    main_rules,
    admin_text,
    admin_rules,
    simple_text
)


# labelers
labelers = (main_text.main_text,
            main_rules.main_rules,
            admin_text.admin_text,
            admin_rules.admin_rules,
            simple_text.common_labeler)

for custom_labeler in labelers:
    labeler.load(custom_labeler)


# объект бота
bot = Bot(api=api,
          labeler=labeler,
          callback=callback,
          state_dispenser=state_dispenser)
    
