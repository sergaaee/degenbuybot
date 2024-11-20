import asyncio
from datetime import timedelta, datetime

from database import Transaction, User, Subscription


async def monitor_transactions(session, bot):
    while True:
        now = datetime.utcnow()
        expired_transactions = (
            session.query(Transaction)
            .filter(Transaction.status == "Pending")
            .filter(Transaction.created_at < now - timedelta(minutes=15))
            .all()
        )

        for transaction in expired_transactions:
            # Удаляем сообщение о платеже (если есть message_id и chat_id, можно удалять сообщение через bot.delete_message)
            user_id = transaction.initiator

            # Уведомляем пользователя об отмене
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if user:
                await bot.send_message(user.telegram_id, "Время на оплату истекло. Транзакция была отменена.")

            # Удаляем транзакцию
            session.delete(transaction)
            session.commit()

        await asyncio.sleep(60)  # Проверяем каждые 60 секунд


async def check_expired_subscriptions(session, bot):
    while True:
        now = datetime.utcnow()
        expired_subs = session.query(Subscription).filter(Subscription.expiration_date < now).all()

        for sub in expired_subs:
            # Исключаем пользователя из чата
            chat_id = sub.chat_id
            user_id = sub.user_id
            await bot.ban_chat_member(chat_id, user_id)

            # Удаляем подписку
            session.delete(sub)
            session.commit()

        await asyncio.sleep(86400)  # Проверять раз в сутки
