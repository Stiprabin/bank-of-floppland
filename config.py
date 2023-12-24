import random
from os import environ


# функция для профиля
def profile(name, surname, user, coffer_cash, user_id):
    return f"📖 Ваш профиль в банке:\n\n" + \
           f"Имя: {name}\n" + \
           f"Фамилия: {surname}\n" + \
           f"Статус: {user['status']}\n" + \
           f"В казне: {int(coffer_cash) // 1000000} млн флопц.\n\n" + \
           f"💶 Баланс:\n\n" + \
           f"{user['cash_f']} флопц.\n" + \
           f"{user['cash_m']} марк.\n\n" + \
           f"💎 ID: {user_id}"


# функция для имперской марки
async def markk(db):
    if "mark" not in await db.keys():
        await db.set("mark", random.randint(51, 61))

    if "marktime" not in await db.keys():
        await db.set("marktime", "Something", 86400)
        mark = int(await db.get("mark"))
        
        new_mark = random.randint(mark - 2, mark + 3)
        await db.set("mark", new_mark)
        
        mark = await db.get("mark")
        await db.rpush("plot", mark)


# функция ограничения для казино
async def casino(db):
    if "casino_time" not in await db.keys():
        # создать временный ключ, если он не существует
        await db.set("casino_time", "Crazy Diamond", 86400)

        # обновить ставки в казино
        for key in await db.keys():
            if key not in CONFIG['IGNORE']:
                await db.hset(key, "limit", 3)


# функция создания казны
async def coffer(db, api):
    # создание казны
    if "coffer_cash" not in await db.keys():
        await db.append("coffer_cash", random.randint(200000000, 300000000))
    else:
        if "coffer_time" not in await db.keys():
            await db.set("coffer_time", "King Crimson", 604800)

            # временный ключ
            if "coffer_list" not in await db.keys():
                await db.lpush("coffer_list", 10000000)
                await db.rpush("coffer_list", 30000000)

            # пополнение казны
            coffer_list = await db.lrange("coffer_list", 0, -1)
            additive = random.randint(int(coffer_list[0]), int(coffer_list[1]))

            await db.incrby("coffer_cash", additive)
            await api.messages.send(peer_id=CONFIG['ADMIN'],
                                    message=f"💰 Казна пополнена на {additive // 1000000} млн флопц!",
                                    random_id=0)


# словарь конфигов
CONFIG = {"TOKEN": environ.get('TOKEN'),
          "CONFIRMATION_TOKEN": environ.get('CONFIRMATION_TOKEN'),
          "SECRET_KEY": environ.get('SECRET_KEY'),
          "URL": environ.get('URL'),
          "ADMIN": int(environ.get('ADMIN')),
          "DB_URL": environ.get('DB_URL'),
          "TITLE": "Карасики",
          "PEER_ID": tuple(range(2000000001, 2000000021)),
          "IGNORE": ("Бронетехника", "Военная авиация", "Артиллерия",
                     "Гражданская техника", "Боевые корабли",
                     "mark", "marktime", "plot", "casino_time",
                     "coffer_cash", "coffer_time", "coffer_list",
                     "products", "timer", "focus")}
    
