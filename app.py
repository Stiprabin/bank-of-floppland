from vk_bot import bot
from vk_api import api
from loguru import logger
from database import Database
from config import (
    CONFIG,
    coffer,
    markk,
    casino
)
from fastapi import (
    FastAPI,
    Request,
    Response,
    BackgroundTasks
)


# инициализация сервера
app = FastAPI()


# запуск сервера
@app.on_event("startup")
async def startup_event():
    logger.info("Setup server...")
    await bot.setup_webhook()


# обработчик событий
@app.post('/')
async def connection(req: Request, background_task: BackgroundTasks):
    event = await req.json()

    async with Database(CONFIG['DB_URL']) as db:
        await coffer(db, api)
        await casino(db)
        await markk(db)

    if 'type' not in event.keys():
        logger.info("Empty request!")
        return Response("not vk")

    if event['secret'] == CONFIG['SECRET_KEY']:

        if event['type'] == "confirmation":
            logger.info(f"Отправлен токен подтверждения: {CONFIG['CONFIRMATION_TOKEN']}")
            return Response(CONFIG['CONFIRMATION_TOKEN'])

        elif event['type'] == "message_new":
            if event['object']['message']['text'][:1] in ('!', '/', '>', '+', '-'):
                event['object']['message']['text'] = event['object']['message']['text'][1:].lower()
            else:
                event['object']['message']['text'] = event['object']['message']['text'].lower()

            background_task.add_task(await bot.process_event(event))

        else:
            background_task.add_task(await bot.process_event(event))

        return Response("ok")
    
