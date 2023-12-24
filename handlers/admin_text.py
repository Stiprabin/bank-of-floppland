import pandas as pd
from database import Database
from plotly.figure_factory import create_table
from keyboards import admin_kb
from io import BytesIO
from config import CONFIG
from state_groups import (
    Recovery,
    Mailing
)
from vkbottle.bot import (
    Message,
    BotLabeler
)
from vk_api import (
    api,
    ctx,
    uploader,
    state_dispenser
)


# labeler
admin_text = BotLabeler()


# все итак очевидно
commands = '''
⚙ Команды администратора:

!налоги -- собрать налоги;

!еретик <ID> -- удалить профиль;

!казна <от> <до> -- установить диапазон пополнения казны;

!заплатить <ID> <суммаФ/М> -- выдать жалование;

!статус <ID> -- установить статус;

!товар <цена> <ID> <количество> <ссылка> -- создать товар;

!уничтожить <ID товара> -- уничтожить товар;

!регистрация <ID> -- создать дефолтный профиль;

!грант <ID> -- выдать грант;

*пустой инвентарь для команды <<!восстановление>> -- <<ничо>>
'''


# панель администратора
@admin_text.private_message(text="админ")
async def admin_panel(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        await message.answer(commands, keyboard=admin_kb)
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# реестр пользователей
@admin_text.private_message(text="реестр")
async def admin_stat(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            stat = "📋 Реестр пользователей:"
            keys = await db.keys()
            df = pd.DataFrame()
            ids = []
            name = []
            surname = []
            status = []
            cash_f = []
            cash_m = []
            limit = []
            for key in keys:
                if key not in CONFIG['IGNORE']:
                    user = await db.hgetall(key)
                    ids.append(key)

                    # имя и фамилия
                    user_info = await api.users.get(key)
                    name.append(user_info[0].first_name)
                    surname.append(user_info[0].last_name)

                    # проблемный статус
                    if user['status'] == "Обыватель":
                        status.append("Стандартный")
                    else:
                        status.append("Нестандартный")

                    cash_f.append(user['cash_f'])
                    cash_m.append(user['cash_m'])
                    limit.append(user['limit'])

            df['ID'] = ids
            df['Имя'] = name
            df['Фамилия'] = surname
            df['Статус'] = status
            df['Флопцы'] = cash_f
            df['Марки'] = cash_m
            df['Ставки в казино'] = limit

            # обработка и отправка таблицы
            fig = create_table(df)
            fig_bytes = fig.to_image(format="png")
            img = BytesIO(fig_bytes)
            img.seek(0)
            image = img.getvalue()
            img.close()
            photo = await uploader.upload(image)
            await message.reply(stat, attachment=photo)
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# реестр статусов
@admin_text.private_message(text="статусы")
async def admin_statuses(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            stat = "📒 Статусы пользователей:\n\n"
            keys = await db.keys()

            for key in keys:
                if key not in CONFIG['IGNORE']:
                    user = await db.hgetall(key)
                    user_info = await api.users.get(key)
                    stat += f"{user_info[0].first_name} {user_info[0].last_name} ({key}) -- {user['status']}\n"

            await message.reply(stat)
            await message.answer("Введите команду !статус <ID пользователя>, чтобы установить статус")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# сбор налогов
@admin_text.private_message(text=["налог", "налоги"])
async def admin_taxes(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            # функция сбора налогов в функции сбора налогов
            async def tax(cash_f, cash_m, text):
                tax_f = round(int(cash_f) * 0.2)
                tax_m = round(int(cash_m) * 0.1)
                cash_f = int(cash_f) - tax_f
                cash_m = int(cash_m) - tax_m

                # сбор налогов
                if tax_m > 0:
                    await db.hset(key, "cash_m", cash_m)
                    await db.incrby("coffer_cash", tax_m * int(await db.get("mark")))
                if tax_f > 0:
                    await db.hset(key, "cash_f", cash_f)
                    await db.incrby("coffer_cash", tax_f)

                # отправка сообщения
                await api.messages.send(peer_id=key,
                                        message=f"📢 С вас собран налог: {text}",
                                        random_id=0)

            for key in await db.keys():
                if key not in CONFIG['IGNORE'] and key != '1':
                    cash_ff = await db.hget(key, "cash_f")
                    cash_mm = await db.hget(key, "cash_m")
                    if round(int(cash_ff) * 0.15) <= 0 < round(int(cash_mm) * 0.05):
                        await tax(cash_ff, cash_mm, f"{round(int(cash_mm) * 0.05)} марк.")
                    elif round(int(cash_ff) * 0.15) > 0 >= round(int(cash_mm) * 0.05):
                        await tax(cash_ff, cash_mm, f"{round(int(cash_ff) * 0.15)} флопц.")
                    elif round(int(cash_ff) * 0.15) > 0 < round(int(cash_mm) * 0.05):
                        await tax(cash_ff, cash_mm, f"{round(int(cash_mm) * 0.05)} марк. и "
                                                    f"{round(int(cash_ff) * 0.15)} флопц.")
                    else:
                        await api.messages.send(peer_id=key,
                                                message=f"📢 Налога не будет, но вы не расстраивайтесь!",
                                                random_id=0)
            await message.answer("✅ Успешно!")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# реестр ключей
@admin_text.private_message(text="ключи")
async def admin_keys(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            keys = await db.keys()
            cap = "🔑 Ключи базы данных:\n\n"
            for key in keys:
                cap += f"{key}\n"

        # вывод реестра
        await message.reply(cap)
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# реестр инвентарей
@admin_text.private_message(text="инвентари")
async def admin_inventory(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        text = "🥬 Инвентари пользователей:\n\n"

        async with Database(CONFIG['DB_URL']) as db:
            for key in (await db.keys()):
                if key not in CONFIG['IGNORE'] and key != '1':
                    val = await db.hgetall(key)
                    if val['inventory'] != '':
                        val = val['inventory'].split('%')[1:]

                        user_info = await api.users.get(key)
                        name = user_info[0].first_name
                        surname = user_info[0].last_name

                        text += f"{name} {surname} ({key}):\n"
                        for v in val:
                            v = v.split('&')
                            text += f"-- {v[0]} (x{v[1]}, ID: {v[2]})\n"
                        text += "\n"

        await message.reply(text)
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# функция восстановления профиля
@admin_text.private_message(text=["восстановление", "восстановить"])
async def admin_recovery_message(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        await state_dispenser.set(message.peer_id, Recovery.ID)
        return "Введите ID пользователя"
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# состояние ID
@admin_text.private_message(state=Recovery.ID)
async def recovery_id(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        ctx.set(Recovery.ID, message.text)
        if ctx.get("recovery_id") in await db.keys():
            await message.answer("⚠ Этот пользователь уже прошел регистрацию")
        else:
            await state_dispenser.set(message.peer_id, Recovery.STATUS)
            return "Введите статус"


# состояние статуса
@admin_text.private_message(state=Recovery.STATUS)
async def recovery_status(message: Message):
    ctx.set(Recovery.STATUS, message.text)
    await state_dispenser.set(message.peer_id, Recovery.CASH_F)
    return "Введите баланс флопцев"


# состояние баланса флопцев
@admin_text.private_message(state=Recovery.CASH_F)
async def recovery_flops(message: Message):
    ctx.set(Recovery.CASH_F, message.text)
    await state_dispenser.set(message.peer_id, Recovery.CASH_M)
    return "Введите баланс марок"


# состояние баланса марок
@admin_text.private_message(state=Recovery.CASH_M)
async def recovery_marks(message: Message):
    ctx.set(Recovery.CASH_M, message.text)
    await state_dispenser.set(message.peer_id, Recovery.LIMIT)
    return "Введите лимит на ставки в казино"


# состояние лимита ставок в казино
@admin_text.private_message(state=Recovery.LIMIT)
async def recovery_limit(message: Message):
    ctx.set(Recovery.LIMIT, message.text)
    await state_dispenser.set(message.peer_id, Recovery.INVENTORY)
    return "Введите инвентарь"


# инвентарь
@admin_text.private_message(state=Recovery.INVENTORY)
async def recovery_inventory(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        if message.text == "ничо":
            message.text = ''

        user = {"status": ctx.get(Recovery.STATUS).title(),
                "cash_f": ctx.get(Recovery.CASH_F),
                "cash_m": ctx.get(Recovery.CASH_M),
                "limit": ctx.get(Recovery.LIMIT),
                "inventory": '%' + message.text.title()}

        await db.hmset(ctx.get(Recovery.ID), user)
        await message.answer("✅ Профиль успешно восстановлен!")

        # и все
        await state_dispenser.delete(message.peer_id)


# лютейшая рассылка
@admin_text.private_message(text="рассылка")
async def mailing_text(message: Message):
    if message.from_id == CONFIG['ADMIN']:
        await state_dispenser.set(message.peer_id, Mailing.TEXT)
        return "Введите текст рассылки"
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# состояние рассылки
@admin_text.private_message(state=Mailing.TEXT)
async def mailing_state(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        keys = await db.keys()
        for key in keys:
            if key not in CONFIG['IGNORE'] and key != '1':
                await api.messages.send(peer_id=key,
                                        message=f"📢 Государственная рассылка:\n\n<<{message.text}>>",
                                        random_id=0)

        await message.answer("✅ Успешно!")
    
