import random
from database import Database
from typing import Tuple
from vk_api import api
from vkbottle.dispatch.rules.base import CommandRule
from vkbottle.bot import (
    Message,
    BotLabeler
)
from config import CONFIG


# labeler
main_rules = BotLabeler()


# переводы
@main_rules.message(CommandRule("перевести", [''], 3))
async def translation_rule(message: Message, args: Tuple[str]):
    async with Database(CONFIG['DB_URL']) as db:
        # данные о пользователе
        user_id = message.from_id
        user_info = await api.users.get(user_id)
        name = user_info[0].first_name
        surname = user_info[0].last_name

        # проверка на наличие профиля
        if await db.exists(user_id):
            if await db.exists(args[0]) and args[0] not in CONFIG['IGNORE']:
                if str(user_id) != args[0]:
                    if args[1].isdigit():
                        # функция перевода в функции перевода
                        async def translation(csh, one_type, two_type):
                            csh = int(csh) - int(args[1])
                            await db.hset(user_id, one_type, csh)
                            await db.hincrby(args[0], one_type, args[1])

                            # отправка сообщений
                            await message.answer("✅ Успешно!")
                            return await api.messages.send(peer_id=args[0], message=f"💸 {name} {surname}"
                                                                                    f" перевел вам {args[1]} "
                                                                                    f"{two_type}", random_id=0)
                        # перевод флопцев
                        if args[2] in ("флопцев", "флопец", "флопца"):
                            cash = await db.hget(user_id, "cash_f")
                            if 0 < int(args[1]) <= int(cash):
                                await translation(cash, "cash_f", "флопц.")
                            else:
                                await message.answer("⚠ Пшел вон отсюда!")

                        # перевод марок
                        elif args[2] in ("марок", "марку", "марки"):
                            cash = await db.hget(user_id, "cash_m")
                            if 0 < int(args[1]) <= int(cash):
                                await translation(cash, "cash_m", "марк.")
                            else:
                                await message.answer("⚠ Пшел вон отсюда!")
                        else:
                            await message.answer("⚠ Некорректный формат!")
                    else:
                        await message.answer("⚠ Пшел вон отсюда!")
                else:
                    await message.answer("⚠ Зачем себе переводить?!")
            else:
                await message.answer("⚠ Пользователь не найден!")
        else:
            await message.answer("⚠ Вы не представились системе!")


# обменная лавка
@main_rules.message(CommandRule("обменять", [''], 2))
async def exchange_rule(message: Message, args: Tuple[str]):
    async with Database(CONFIG['DB_URL']) as db:
        # данные о пользователе
        user_id = message.from_id

        if await db.exists(user_id):
            if args[0].isdigit():

                # обмен марок
                if args[1] in ("марок", "марки", "марку"):
                    marks = await db.hget(user_id, "cash_m")
                    if int(marks) >= int(args[0]) > 0:
                        flops = int(args[0]) * int(await db.get("mark"))
                        marks = int(marks) - int(args[0])
                        await db.hincrby(user_id, "cash_f", flops)
                        await db.hset(user_id, "cash_m", marks)
                        await message.answer(f"✅ Успешно! Вы получили {flops} флопц.")
                    else:
                        await message.answer("⚠ Иди на завод работать!")

                # обмен флопцев
                elif args[1] in ("флопцев", "флопца", "флопец"):
                    flops = await db.hget(user_id, "cash_f")
                    mark = await db.get("mark")

                    # проверка ценности марки
                    if int(flops) >= int(args[0]) > 0:
                        if int(args[0]) < int(mark):
                            await message.answer("⚠ Введенная сумма меньше стоимости марки!")
                        else:
                            marks = int(args[0]) // int(mark)
                            remainder = int(args[0]) % int(mark)
                            flops = int(flops) - int(args[0]) + remainder
                            await db.hincrby(user_id, "cash_m", marks)
                            await db.hset(user_id, "cash_f", flops)

                            # адекватизация остатка
                            if remainder != 0:
                                await message.answer(f"✅ Успешно! Вы получили {marks} марк. и {remainder} флопц.")
                            else:
                                await message.answer(f"✅ Успешно! Вы получили {marks} марк.")
                    else:
                        await message.answer("⚠ Иди на завод работать!")
                else:
                    await message.answer("⚠ Некорректный формат!")
            else:
                await message.answer("⚠ Вы высрали дичь!")
        else:
            await message.answer("⚠ Вы не представились системе!")


# приобретение товаров
@main_rules.message(CommandRule("купить", [''], 1))
async def buy_rule(message: Message, args: Tuple[str]):
    async with Database(CONFIG['DB_URL']) as db:
        if await db.exists(message.from_id):
            if args[0] in await db.hkeys("products"):
                # элементы товара
                product = await db.hget("products", args[0])
                product = product.split('%')

                # запрещаю вам покупать свои товары!
                if str(message.from_id) != product[2]:
                    # проверить пользователя на наличие нужной суммы
                    if int(product[1]) <= int(await db.hget(message.from_id, "cash_f")):
                        # казначейский ли товар? денежный обмен
                        if product[2] == "coffer_cash":
                            await db.incrby("coffer_cash", product[1])
                        else:
                            salary = round(int(product[1]) * 0.7)
                            await db.hincrby(product[2], "cash_f", salary)
                            await db.incrby("coffer_cash", round(int(product[1]) * 0.3))

                        await db.hset(message.from_id, "cash_f",
                                      int(await db.hget(message.from_id, "cash_f")) - int(product[1]))

                        # инвентарь
                        products = (await db.hget(message.from_id, "inventory")).split('%')

                        # список ID товаров в инвентаре
                        ids = list()
                        for p in products[1:]:
                            ids.append(p.split('&')[2])

                        if args[0] not in ids:
                            await db.hset(message.from_id, "inventory",
                                          await db.hget(message.from_id, "inventory") + '%' + product[0] + '&' + '1'
                                          + '&' + args[0])
                        else:
                            index = 0
                            for p in products[1:]:
                                index += 1
                                p = p.split('&')
                                if p[2] == args[0]:
                                    p[1] = str(int(p[1]) + 1)
                                    p = '&'.join(p)
                                    products[index] = p
                                    break

                            await db.hset(message.from_id, "inventory", '%'.join(products))

                        # уменьшение партии товара
                        product[3] = str(int(product[3]) - 1)
                        if product[3] == '0':
                            await db.hdel("products", args[0])
                        else:
                            await db.hset("products", args[0], '%'.join(product))

                        # успех (азатище имба)
                        await message.answer("✅ Успешно!")

                        # оповестить продавца
                        user_info = await api.users.get(message.from_id)
                        name, surname, text = user_info[0].first_name, user_info[0].last_name, "Вы заработали:"
                        if product[2] == "coffer_cash":
                            product[2] = CONFIG['ADMIN']
                            text = "Казна пополнена на:"
                            salary = product[1]

                        await api.messages.send(peer_id=product[2],
                                                message=f"📢 {name} {surname} приобрел <<{product[0]}>>!\n"
                                                        f"{text} {salary} флопц.",
                                                random_id=0)
                    else:
                        await message.answer("⚠ Недостаточно флопцев!")
                else:
                    await message.answer("⚠ Я вам запрещаю покупать свой товар!")
            else:
                await message.answer("⚠ Это шо за товар?")
        else:
            await message.answer("⚠ Вы не представились системе!")


# удолыть товар
@main_rules.message(CommandRule("удалить", [''], 1))
@main_rules.message(CommandRule("удолыть", [''], 1))
async def del_rule(message: Message, args: Tuple[str]):
    async with Database(CONFIG['DB_URL']) as db:
        products = (await db.hget(message.from_id, "inventory")).split('%')
        index = 0
        counter = 0

        for i in products[1:]:
            index += 1
            for j in i.split('&')[2]:

                if args[0] == j:
                    counter += 1
                    product = products[index].split('&')

                    if product[1] == '1':
                        del products[index]
                    else:
                        product[1] = str(int(product[1]) - 1)
                        products[index] = '&'.join(product)
                        await db.hset(message.from_id, "inventory", '%'.join(products))

        if counter > 0:
            await db.hset(message.from_id, "inventory", '%'.join(products))
            await message.answer("✅ Успешно!")
        else:
            await message.answer("⚠ Это шо за предмет?")


# казино
@main_rules.message(CommandRule("рулетка", [''], 2))
async def casino_rule(message: Message, args: Tuple[str]):
    async with Database(CONFIG['DB_URL']) as db:
        # данные о пользователе
        user_id = message.from_id
        if await db.exists(user_id):

            # поиграл и хватит
            if int(await db.hget(user_id, "limit")) <= 0:
                await message.reply("🎱 Поиграл и хватит. Жди завтрашнего дня")
            else:
                # варианты для ставки
                options = {"even": ("чет", "чёт", "четное", "чётное"),
                           "odd": ("нечётное", "нечет", "нечетное", "нечёт"),
                           "red": ("красный", 'к'),
                           "black": ("черный", "чёрный", 'ч'),
                           "one halve": "1-18",
                           "two halve": "19-36",
                           "one third": "1st",
                           "two third": "2nd",
                           "three third": "3rd",
                           "one dozen": "1-12",
                           "two dozen": "13-24",
                           "three dozen": "25-36",
                           "number": tuple(range(1, 37))}

                def roulette():
                    colors = {'red': (1, 3, 5, 7, 9, 12, 14, 16, 19, 21, 23, 25, 27, 30, 32, 34, 36, 0),
                              'black': (2, 4, 6, 8, 11, 13, 15, 17, 20, 22, 24, 26, 29, 28, 31, 33, 35)}

                    random_color = random.choice(tuple(colors))
                    color = list()
                    color.append(random.choice(colors[random_color]))
                    color.append(random_color)
                    return color

                # функция поражения
                async def db_defeat(type_num):
                    csh = await db.hget(user_id, "cash_f")
                    csh = int(csh) - int(args[0])
                    await db.hset(user_id, "cash_f", csh)
                    await db.hset(user_id, "limit", int(await db.hget(user_id, "limit")) - 1)
                    await db.incrby("coffer_cash", args[0])
                    await message.reply(f"🎱 Шар приземлился на {num[0]}, {type_num}. Вы проиграли и теряете "
                                        f"ставку!\nОсталось ставок: {await db.hget(user_id, 'limit')}")

                # функция победы
                async def db_win(factor, type_num):
                    csh = await db.hget(user_id, "cash_f")
                    csh = int(csh) - int(args[0]) + int(args[0]) * factor
                    await db.hset(user_id, "cash_f", csh)
                    await db.hset(user_id, "limit", int(await db.hget(user_id, "limit")) - 1)
                    await message.reply(f"🎱 Шар приземлился на {num[0]}, {type_num}. Вы получаете {win} "
                                        f"флопц.!\nОсталось ставок: {await db.hget(user_id, 'limit')}")

                if args[0].isdigit() >= 0:
                    if int(await db.hget(user_id, "cash_f")) >= int(args[0]) > 0:
                        if args[1] in str(options.values())[13:-2]:
                            num = roulette()
                            if num[0] == 0:
                                await message.answer("🎱 Шар приземлился на ноль! Вы остаетесь при своих")
                            else:
                                # четность
                                if args[1] in options['even']:
                                    win = int(args[0]) * 2
                                    if num[0] % 2 == 0:
                                        await db_win(2, "число четное")
                                    else:
                                        await db_defeat("число нечетное")

                                # нечетность
                                elif args[1] in options['odd']:
                                    win = int(args[0]) * 2
                                    if num[0] % 2 == 1:
                                        await db_win(2, "число нечетное")
                                    else:
                                        await db_defeat("число четное")

                                # красный
                                elif args[1] in options['red']:
                                    win = int(args[0]) * 2
                                    if num[1] == "red":
                                        await db_win(2, "цвет красный")
                                    else:
                                        await db_defeat("цвет черный")

                                # черный
                                elif args[1] in options['black']:
                                    win = int(args[0]) * 2
                                    if num[1] == "black":
                                        await db_win(2, "цвет черный")
                                    else:
                                        await db_defeat("цвет красный")

                                # первая половина
                                elif args[1] == options['one halve']:
                                    win = int(args[0]) * 2
                                    if int(num[0]) in tuple(range(1, 19)):
                                        await db_win(2, "половина 1-18")
                                    else:
                                        await db_defeat("половина 19-36")

                                # вторая половина
                                elif args[1] == options['two halve']:
                                    win = int(args[0]) * 2
                                    if int(num[0]) in tuple(range(19, 37)):
                                        await db_win(2, "половина 19-36")
                                    else:
                                        await db_defeat("половина 1-18")

                                # первая треть
                                elif args[1] == options['one third']:
                                    win = int(args[0]) * 3
                                    if int(num[0]) in tuple(range(1, 35, 3)):
                                        await db_win(3, "первая колонна")
                                    elif int(num[0]) in tuple(range(2, 36, 3)):
                                        await db_defeat("вторая колонна")
                                    else:
                                        await db_defeat("третья колонна")

                                # вторая треть
                                elif args[1] == options['two third']:
                                    win = int(args[0]) * 3
                                    if int(num[0]) in tuple(range(2, 36, 3)):
                                        await db_win(3, "вторая колонна")
                                    elif int(num[0]) in tuple(range(1, 35, 3)):
                                        await db_defeat("первая колонна")
                                    else:
                                        await db_defeat("третья колонна")

                                # тр*тья треть
                                elif args[1] == options['three third']:
                                    win = int(args[0]) * 3
                                    if int(num[0]) in tuple(range(3, 37, 3)):
                                        await db_win(3, "третья колонна")
                                    elif int(num[0]) in tuple(range(2, 36, 3)):
                                        await db_defeat("вторая колонна")
                                    else:
                                        await db_defeat("первая колонна")

                                # первая дюжина
                                elif args[1] == options['one dozen']:
                                    win = int(args[0]) * 3
                                    if int(num[0]) in tuple(range(1, 13)):
                                        await db_win(3, "первая дюжина")
                                    elif int(num[0]) in tuple(range(13, 25)):
                                        await db_defeat("вторая дюжина")
                                    else:
                                        await db_defeat("третья дюжина")

                                # вторая дюжина
                                elif args[1] == options['two dozen']:
                                    win = int(args[0]) * 3
                                    if int(num[0]) in tuple(range(13, 25)):
                                        await db_win(3, "вторая дюжина")
                                    elif int(num[0]) in tuple(range(1, 13)):
                                        await db_defeat("первая дюжина")
                                    else:
                                        await db_defeat("третья дюжина")

                                # третья дюжина
                                elif args[1] == options['three dozen']:
                                    win = int(args[0]) * 3
                                    if int(num[0]) in tuple(range(25, 37)):
                                        await db_win(3, "третья дюжина")
                                    elif int(num[0]) in tuple(range(13, 25)):
                                        await db_defeat("вторая дюжина")
                                    else:
                                        await db_defeat("первая дюжина")

                                # точное число
                                elif args[1].isdigit():
                                    if int(args[1]) in options['number']:
                                        win = int(args[0]) * 36
                                        if num[0] == int(args[1]):
                                            await db_win(36, f"ваше число -- {args[1]}")
                                        else:
                                            await db_defeat(f"ваше число -- {args[1]}")
                        else:
                            await message.answer("⚠ Некорректный формат!")
                    else:
                        await message.answer(random.choice(("⚠ Ви визріли дичину!", "⚠ Вы высрали дичь!",
                                                            "⚠ Вы высралі дзічыну!", "⚠ Jūs izjaukāt spēli!",
                                                            "⚠ Зајебао си игру!")))
                else:
                    await message.answer(random.choice(("⚠ Ви визріли дичину!", "⚠ Вы высрали дичь!",
                                                        "⚠ Вы высралі дзічыну!", "⚠ Jūs izjaukāt spēli!",
                                                        "⚠ Зајебао си игру!")))
        else:
            await message.answer("⚠ Вы не представились системе!")
    
