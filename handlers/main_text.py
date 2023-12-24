import random
import matplotlib.pyplot as plt
from urllib.request import urlopen
from PIL import Image
from database import Database
from config import (
    CONFIG,
    profile
)
from vkbottle import (
    KeyboardButtonColor,
    Keyboard,
    Text
)
from vkbottle.bot import (
    BotLabeler,
    Message
)
from keyboards import (
    one_menu_kb,
    two_menu_kb
)
from vk_api import (
    api,
    uploader,
    image_handler
)


# labeler
main_text = BotLabeler()


commands = '''
📜 Команды простых смертных:

!перевести <ID> <сумма> <флопцев/марок> -- перевести флопцы или марки;

!обменять <сумма> <флопцев/марок> - обменять флопцы на марки или наоборот;

!купить <ID товара> -- купить товар;

!удолыть <ID товара> -- уничтожить товар
'''


# меню
@main_text.message(text=["меню", "начать", "команды"])
async def menu_text(message: Message):
    if message.peer_id in CONFIG['PEER_ID']:
        await message.reply(commands)
    else:
        await message.reply(commands, keyboard=one_menu_kb)


# динамизация меню
@main_text.message(payload={'cmd': 'one_menu'})
async def one_dynamic(message: Message):
    await message.answer("Панель обновлена!", keyboard=two_menu_kb)


@main_text.message(payload={'cmd': 'two_menu'})
async def two_dynamic(message: Message):
    await message.answer("Панель обновлена!", keyboard=one_menu_kb)


# казино
@main_text.message(text="казино")
async def casino_message(message: Message):
    await message.reply('''🎰 Добро пожаловать в казино Стипецка! Вы можете сделать ставку в рулетке, используя 
команду !рулетка <ставка> <сумма флопцев> <на что ставите> (!рулетка 600 1-18)

💸 На что поставить?
[x36] На число от 1 до 36
[x3] На дюжину (1-12, 13-24, 25-36)
[x3] На колонну (1st, 2nd, 3rd)
[x2] На половину (1-18, 19-36)
[x2] На четность или нечетность (чет / нечет)
[x2] На цвет (красный / черный)
''')


# регистрация и отправка профиля
@main_text.message(text=["счет", "счёт", "профиль"])
async def profile_text(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        if await db.exists(message.from_id):
            # данные о пользователе
            user_info = await api.users.get(message.from_id)
            name = user_info[0].first_name
            surname = user_info[0].last_name

            # отправить профиль
            user = await db.hgetall(message.from_id)
            coffer_cash = await db.get('coffer_cash')

            if message.peer_id in CONFIG['PEER_ID']:
                await message.reply(profile(name, surname, user, coffer_cash, message.from_id))
            else:
                await message.reply(profile(name, surname, user, coffer_cash, message.from_id),
                                    keyboard=one_menu_kb)
        else:
            if message.peer_id in CONFIG['PEER_ID']:
                await message.reply("⚠ Регистрация осуществляется в ЛС бота")
            else:
                try:
                    # URL полученного изображения
                    url = message.attachments[0].photo.sizes[-5].url
                    await message.reply("✅ Заявка успешно отправлена! Ожидайте")

                    # обработка полученного изображения
                    image = Image.open(urlopen(url))
                    image.save(image_handler, "PNG")
                    image.close()
                    image_handler.seek(0)

                    # клавиатура для регистрации профиля
                    reg_menu_mb = (
                        Keyboard(one_time=False, inline=True)
                        .add(Text(f"регистрация {message.from_id}"), color=KeyboardButtonColor.PRIMARY)
                    ).get_json()

                    # отправка базы
                    user_info = await api.users.get(message.from_id)
                    name, surname = user_info[0].first_name, user_info[0].last_name
                    await api.messages.send(peer_id=CONFIG['ADMIN'],
                                            message=f"🕓 {name} {surname} отправил заявку на регистрацию профиля!",
                                            keyboard=reg_menu_mb,
                                            attachment=await uploader.upload(image_handler.getvalue()),
                                            random_id=0)
                except IndexError:
                    await message.answer("⚠ Прикрепите паспорт Шлёпляндии или СГШ")


# инвентарь
@main_text.message(text="инвентарь")
async def inventory_text(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        if await db.exists(message.from_id):
            user = await db.hgetall(message.from_id)
            if user['inventory'] == '':
                await message.answer("📋 Ваш инвентарь пуст!")
            else:
                text = "📋 Ваш инвентарь:\n\n"
                inventory = user['inventory'].split('%')
                for i in inventory[1:]:
                    i = i.split('&')
                    text += f"-- {i[0]} (ID: {i[2]}, x{i[1]})\n"
                await message.answer(text)
        else:
            await message.answer("⚠ Вы не представились системе!")


# ID пользователей
@main_text.message(text=["id пользователей", "айди"])
async def id_text(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        keys = await db.keys()
        cap = "🔑 ID пользователей:\n\n"
        for key in keys:
            if key not in CONFIG['IGNORE']:
                user_info = await api.users.get(int(key))
                cap += f"{user_info[0].first_name} {user_info[0].last_name} -- {key}\n"

        await message.reply(cap)


# шлОпримский рыночек
@main_text.message(text=["рынок", "рыночек", "товары"])
async def market_message(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        text = "📦 Список товаров на Шлёпримском рынке:\n\n"
        products = await db.hgetall("products")

        # имба итерация
        for key, val in products.items():
            val = val.split('%')
            if val[2] == "coffer_cash":
                val[2] = "Казначейский товар"
            text += f"Название: {val[0]}\n" \
                    f"Цена: {val[1]} флопц.\n" \
                    f"Количество: {val[3]}\n" \
                    f"ID товара: {key}\n" \
                    f"ID продавца: {val[2]}\n" \
                    f"[{val[4]}|Пост]\n\n"

        text += "Чтобы купить товар, введите команду:\n!купить <ID>"
        await message.answer(text)


# имперская марка и ее курс
@main_text.message(text=["курс марки", "курс", "марка"])
async def mark_message(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        # функция сохранения истории курса
        async def array_db():
            point = await db.get("mark")
            await db.rpush("plot", point)

        async def send_message(sign, image=None):
            return await message.answer(f"{sign} Курс марки к флопцу: 1 имперская марка равна {await db.get('mark')} "
                                        f"флопц.\n\n"
                                        f"До обновления курса: {round(int(await db.ttl('marktime')) / 60)} мин.",
                                        attachment=image)

        # проверка на наличие нужных ключей
        if "mark" not in await db.keys():
            await db.set("mark", random.randint(51, 61))

        if 'plot' not in await db.keys():
            await array_db()

        # график курса марки
        async def graphic(color):
            length = await db.llen("plot")
            arr = await db.lrange("plot", 0, -1)

            # очистка истории
            if int(length) >= 250:
                del arr[0:100]
                await db.delete("plot")
                for arrr in arr:
                    await db.rpush("plot", arrr)
                length = await db.llen("plot")

            array = list()
            for arrays in arr:
                arrays = int(arrays)
                array.append(arrays)

            # создание графика
            plt.figure()
            plt.title("График курса ИМПЭРСКОЙ марки")
            plt.plot(tuple(range(0, int(length))), array, alpha=0.8, color=color, linewidth=2)
            plt.grid()
            plt.ylabel("Стоимость во флопцах")
            plt.savefig(image_handler, format="png")
            plt.close()

            # VK-загрузчик
            img = image_handler.getvalue()
            image_handler.seek(0)
            photo = await uploader.upload(img)
            return photo

        # отправка курса
        if "marktime" in await db.keys():
            await send_message("⏳", await graphic("tab:green"))
        else:
            # установка временного ключа
            await db.set("marktime", "Something", 86400)
            mark = int(await db.get("mark"))

            # изменение курса
            new_mark = random.randint(mark - 2, mark + 2)
            await db.set("mark", new_mark)
            await array_db()

            if new_mark > mark:
                await send_message("📈", await graphic("tab:red"))
            elif new_mark == mark:
                await send_message("📃", await graphic("tab:green"))
            else:
                await send_message("📉", await graphic("tab:blue"))
    
