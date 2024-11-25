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

            transaction.status = "Expired"
            session.commit()

        await asyncio.sleep(60)  # Проверяем каждые 60 секунд


async def check_expired_subscriptions(session, bot):
    while True:
        now = datetime.utcnow()
        three_days_from_now = now + timedelta(days=3)

        # Проверяем истекшие подписки
        expired_subs = session.query(Subscription).filter(Subscription.expiration_date < now).all()

        for sub in expired_subs:
            # Исключаем пользователя из чата
            chat_id = sub.chat_id
            user_id = sub.user_id
            try:
                await bot.ban_chat_member(chat_id, user_id)
            except Exception:
                print(f"Не удалось кикнуть пользователя {user_id}")

            # Удаляем подписку
            session.delete(sub)
            session.commit()

            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"Ваша подписка на чат истекла."
                )
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

        # Проверяем подписки, которые истекают через 3 дня
        about_to_expire_subs = session.query(Subscription).filter(
            Subscription.expiration_date >= now,
            Subscription.expiration_date <= three_days_from_now
        ).all()

        for sub in about_to_expire_subs:
            user_id = sub.user_id
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"Ваша подписка истекает через 3 дня! Пожалуйста, продлите её, чтобы не потерять доступ."
                )
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

        await asyncio.sleep(86400)  # Проверять раз в сутки
