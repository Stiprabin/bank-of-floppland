from vkbottle import BaseStateGroup


# установление статуса
class Status(BaseStateGroup):
    TEXT = "text"


# рассылка
class Mailing(BaseStateGroup):
    TEXT = "text"


# выдача жалований
class Salaries(BaseStateGroup):
    TEXT = "text"


# создание товара
class Product(BaseStateGroup):
    NAME = "name"


# выдача грантов
class Grants(BaseStateGroup):
    COFFER = "coffer"
    SUMMA = "summa"
    TEXT = "text"


# восстановление профиля
class Recovery(BaseStateGroup):
    ID = "id"
    STATUS = "status"
    CASH_F = "cash_f"
    CASH_M = "cash_m"
    LIMIT = "limit"
    INVENTORY = "inventory"
    
