import random
from typing import Tuple
from database import Database
from grants import GrantCreating
from vkbottle.dispatch.rules.base import CommandRule
from vkbottle.bot import (
    Message,
    BotLabeler
)
from config import (
    CONFIG,
    profile
)
from state_groups import (
    Grants,
    Status,
    Product,
    Salaries
)
from vk_api import (
    api,
    ctx,
    uploader,
    state_dispenser
)


# labeler
admin_rules = BotLabeler()


# удаление профиля
@admin_rules.private_message(CommandRule("еретик", [''], 1))
async def deleting_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            if await db.exists(args[0]):
                await db.delete(args[0])
                await message.answer("✅ Успешно!")
            else:
                await message.answer("⚠ Пользователь не найден!")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# диапазон для казны
@admin_rules.private_message(CommandRule("казна", [''], 2))
async def coffer_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            await db.delete("coffer_list")
            await db.lpush("coffer_list", int(args[0]))
            await db.rpush("coffer_list", int(args[1]))
            await message.answer("✅ Успешно!")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# выдача жалований
@admin_rules.private_message(CommandRule("заплатить", [''], 2))
async def salaries_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        ctx.set("salaries_id", args[0])
        ctx.set("salaries_cash", args[1])
        await state_dispenser.set(message.peer_id, Salaries.TEXT)
        return "Введите комментарий к жалованию"
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# состояние комментария к жалованию
@admin_rules.private_message(state=Salaries.TEXT)
async def salaries_state(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        # хранилище CTX
        salaries_id = ctx.get("salaries_id")
        cash = ctx.get("salaries_cash")

        if await db.exists(salaries_id) and (salaries_id not in CONFIG['IGNORE']):
            # вырезать тип валюты
            salary = int(cash[0:-1])

            # выдача и отбор флопцев
            if cash[-1] in ('f', 'ф'):
                await db.hincrby(salaries_id, "cash_f", salary)
                await db.set("coffer_cash", int(await db.get("coffer_cash")) - salary)

                if salary > 0:
                    await api.messages.send(peer_id=salaries_id,
                                            message=f"💸 Вам выдано жалование: {salary} флопц."
                                                    f"\n\nКомментарий: <<{message.text}>>",
                                            random_id=0)
                if salary < 0:
                    await api.messages.send(peer_id=salaries_id,
                                            message=f"📉 У вас отобрали: {str(salary)[1:]} флопц."
                                                    f"\n\nКомментарий: <<{message.text}>>",
                                            random_id=0)

                await message.answer("✅ Успешно!")

            # выдача и отбор имперских марок
            elif cash[-1] in ('m', 'м'):
                await db.hincrby(salaries_id, "cash_m", salary)
                await db.set("coffer_cash", int(await db.get("coffer_cash")) - salary * int(await db.get("mark")))

                if salary > 0:
                    await api.messages.send(peer_id=salaries_id,
                                            message=f"💸 Вам выдано жалование: {salary} марк."
                                                    f"\n\nКомментарий: <<{message.text}>>",
                                            random_id=0)
                if salary < 0:
                    await api.messages.send(peer_id=salaries_id,
                                            message=f"📉 У вас отобрали: {str(salary)[1:]} марк."
                                                    f"\n\nКомментарий: <<{message.text}>>",
                                            random_id=0)

                await message.answer("✅ Успешно!")
            else:
                await message.answer("⚠ Некорректный формат!")
        else:
            await message.answer("⚠ Пользователь не найден!")

        # и все
        await state_dispenser.delete(message.peer_id)


# установка статуса
@admin_rules.private_message(CommandRule("статус", [''], 1))
async def status_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        ctx.set("status_id", args[0])
        await state_dispenser.set(message.peer_id, Status.TEXT)
        return "Введите статус"
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# состояние статуса
@admin_rules.private_message(state=Status.TEXT)
async def status_state(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        # хранилище CTX
        new_status = message.text.title()
        status_id = ctx.get("status_id")

        if await db.exists(status_id) and (status_id not in CONFIG['IGNORE']):
            old_status = await db.hget(status_id, "status")
            await api.messages.send(peer_id=status_id,
                                    message=f"📢 Ваш статус в банке изменен с <<{old_status.title()}>> "
                                            f"на <<{new_status}>>",
                                    random_id=0)
            await db.hset(status_id, "status", new_status)
            await message.answer("✅ Успешно!")
        else:
            await message.answer("⚠ Пользователь не найден!")

        # закрытие машины состояний
        await state_dispenser.delete(message.peer_id)


# создание товара
@admin_rules.private_message(CommandRule("товар", [''], 5))
async def product_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        if args[0].isdigit() and args[2].isdigit():
            ctx.set("product_cash", args[0])
            ctx.set("product_salesman", args[1])
            ctx.set("product_party", args[2])
            ctx.set("product_link", args[3])
            ctx.set("product_id", args[4])
            await state_dispenser.set(message.peer_id, Product.NAME)
            return "Введите название товара"
        else:
            await message.answer("⚠ Пiшов нахрен, Iрис!")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# создание товара ищо раз
@admin_rules.private_message(state=Product.NAME)
async def product_state(message: Message):
    async with Database(CONFIG['DB_URL']) as db:
        # мудреная строка товара
        product = message.text.title() + '%' + \
                  ctx.get("product_cash") + '%' + \
                  ctx.get("product_salesman") + '%' + \
                  ctx.get("product_party") + '%' + \
                  ctx.get("product_link")

        # создание товара
        await db.hset("products", ctx.get("product_id"), product)
        await message.answer("✅ Успешно!")

        # оповещение продавца
        if ctx.get("product_salesman") != "coffer_cash":
            await api.messages.send(peer_id=ctx.get("product_salesman"),
                                    message=f"✅ Ваш товар <<{message.text.title()}>> успешно выставлен на рынке!\n"
                                            f"Стоимость: {ctx.get('product_cash')} флопц.\n"
                                            f"Количество: {ctx.get('product_party')}",
                                    random_id=0)

        # закрытие машины состояний
        await state_dispenser.delete(message.peer_id)


# удаление товара
@admin_rules.private_message(CommandRule("уничтожить", [''], 1))
async def destroy_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            if args[0] in await db.hkeys("products"):
                await db.hdel("products", args[0])
                await message.answer("✅ Успешно!")
            else:
                await message.answer("⚠ Не знаю такого товара!")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# регистрация
@admin_rules.private_message(CommandRule("регистрация", [''], 1))
async def reg_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            if await db.exists(args[0]):
                await message.answer("⚠ Эта персона уже зарегистрирована!")
            else:
                # данные о пользователе
                user_info = await api.users.get(args[0])
                name = user_info[0].first_name
                surname = user_info[0].last_name

                # создать профиль
                user = {"status": "Обыватель",
                        "cash_f": 0,
                        "cash_m": 10,
                        "limit": 3,
                        "inventory": ''}

                await db.hmset(args[0], user)
                await message.answer("✅ Регистрация успешно завершена!")

                # отправить профиль
                user = await db.hgetall(args[0])
                coffer_cash = await db.get('coffer_cash')
                await api.messages.send(peer_id=args[0],
                                        message="✅ Регистрация успешно завершена!",
                                        random_id=0)
                await api.messages.send(peer_id=args[0],
                                        message=profile(name, surname, user, coffer_cash, args[0]),
                                        random_id=0)
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# выдача грантов
@admin_rules.private_message(CommandRule("грант", [''], 1))
async def grants_rule(message: Message, args: Tuple[str]):
    if message.from_id == CONFIG['ADMIN']:
        async with Database(CONFIG['DB_URL']) as db:
            if await db.exists(args[0]) and args[0] not in CONFIG['IGNORE']:
                ctx.set("grant_id", args[0])
                await state_dispenser.set(message.peer_id, Grants.COFFER)
                return "Введите сумму, которую нужно выделить из казны"
            else:
                await message.answer("⚠ Пользователь не найден!")
    else:
        await message.answer("⚠ Вы не являетесь Имперским казначеем!")


# выделяемые деньги
@admin_rules.private_message(state=Grants.COFFER)
async def grants_coffer(message: Message):
    ctx.set(Grants.COFFER, message.text)
    await state_dispenser.set(message.peer_id, Grants.SUMMA)
    return "Введите сумму, которую нужно указать на гранте (па приколу)"


# пафосный текст
@admin_rules.private_message(state=Grants.SUMMA)
async def grants_summa(message: Message):
    ctx.set(Grants.SUMMA, message.text)
    await state_dispenser.set(message.peer_id, Grants.TEXT)
    return "Введите сообщение для отправителя"


# final round
@admin_rules.private_message(state=Grants.TEXT)
async def grants_pil(message: Message):
    # хранилище CTX и данные о пользователе
    user_id = ctx.get("grant_id")
    coffer = int(ctx.get(Grants.COFFER))
    summa = ctx.get(Grants.SUMMA).upper()
    user_info = await api.users.get(user_id)
    name = user_info[0].first_name
    surname = user_info[0].last_name

    # выделение денег из казны
    async with Database(CONFIG['DB_URL']) as db:
        await db.set("coffer_cash", int(await db.get("coffer_cash")) - coffer)

    # базированный объект базированного класса
    gr = GrantCreating("images/ticket.png")

    # создание гранта
    gr.add_font("fonts/AlumniSans-SemiBold.ttf", 70)
    gr.add_text((442, 937), str(random.randint(100000000, 1000000000)), (251, 247, 222))

    gr.add_font("fonts/Bitter-Medium.ttf", 45)
    gr.add_text((230, 775), user_id, (82, 81, 65))
    gr.add_text((720, 775), f"{name} {surname}", (82, 81, 65))
    gr.add_text((230, 660), summa, (82, 81, 65))

    photo = await uploader.upload(gr.upload())

    # отправка гранта
    await api.messages.send(peer_id=user_id,
                            message=f"🗞 Казначейство выдало вам грант с репликой:\n\n<<{message.text}>>",
                            attachment=photo,
                            random_id=0)
    await message.answer("✅ Успешно!")

    # закрытие машины состояний
    await state_dispenser.delete(message.peer_id)
    
