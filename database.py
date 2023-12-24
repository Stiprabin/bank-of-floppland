from aioredis import from_url


# класс для работы с базой данных
class Database:
    """инициализация"""
    def __init__(self, host):
        self.host = host

    """создание объекта Redis"""
    async def __aenter__(self):
        self.db = from_url(url=self.host,
                           decode_responses=True)
        return self.db

    """закрытие объекта Redis"""
    async def __aexit__(self, exc_type, exc, tb):
        await self.db.close()
