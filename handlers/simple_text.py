from vkbottle.bot import Message, BotLabeler
from random import choice


# labeler
common_labeler = BotLabeler()


# проверка бота на труп
@common_labeler.message(text=["бот шлепа", "бот шлёпа", "паровой танк"])
async def bot_text(message: Message):
    await message.answer(choice(('Я тут', 'На базе', 'Эт я', 'Шо надо')))


# база
@common_labeler.message(text=["саддам", "садам"])
async def saddam_text(message: Message):
    await message.reply('''Все ругают тебя
Дорогой мой Саддам,
Но в обиду тебя
Никому я не дам.
За ресурсы в Dogестане
Ты в курсе один,
И в борьбе за них
Ты просрал весь бюджет
Саддам Хусейн, привет Саддам,
Привет бродягам и ворам,
А ресурсы по трубам бегут там,
Живет Догим, цветет Шлёприм...''')


# тож база
@common_labeler.message(text=['а', 'и', "чо", "пон", "лан", "ок", "ичо"])
async def dart_text(message: Message):
    await message.reply("❗Вы были взломаны тульским филиалом жожо-аненербе. "
                        "Для возможности пользоваться ботом дальше "
                        "вышлите в рейхстаг все артефакты-свидетельства величия арийской расы")


# прощай... Дин
@common_labeler.message(text="ej dirst!")
async def daniel_text(message: Message):
    await message.reply("Kad līķis būšu es, tad vairāk nedzeršu!")


# прощай... Дин
@common_labeler.message(text="дин")
async def din_text(message: Message):
    await message.answer("ДОН")
    
