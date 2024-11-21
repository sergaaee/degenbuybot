import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

from async_tasks import check_expired_subscriptions, monitor_transactions
from database import init_db

load_dotenv()

# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.getenv('BOT_TOKEN')

Session = init_db()
session = Session()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()



async def main():
    # Инициализация
    from callbacks import router
    from routers import payments_router
    init_db()
    dp.include_routers(router, payments_router)

    # Запуск проверки подписок
    asyncio.create_task(check_expired_subscriptions(session, bot))
    asyncio.create_task(monitor_transactions(session, bot))

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
