from vkbottle import (
    KeyboardButtonColor,
    Keyboard,
    Text
)


# первая клавиатура для меню
one_menu_kb = (
    Keyboard(one_time=False, inline=False)
    .add(Text("счет"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("казино"), color=KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("айди"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("вперед", payload={'cmd': 'one_menu'}), color=KeyboardButtonColor.SECONDARY)
).get_json()


# вторая клавиатура для меню
two_menu_kb = (
    Keyboard(one_time=False, inline=False)
    .add(Text("рынок"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("курс"), color=KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("инвентарь"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("назад", payload={'cmd': 'two_menu'}), color=KeyboardButtonColor.SECONDARY)
).get_json()


# клавиатура администратора
admin_kb = (
    Keyboard(one_time=False, inline=False)
    .add(Text("инвентари"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("статусы"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("ключи"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("восстановление"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("реестр"), color=KeyboardButtonColor.SECONDARY)
    .add(Text("рассылка"), color=KeyboardButtonColor.SECONDARY)
).get_json()
    
