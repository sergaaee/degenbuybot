from sqlalchemy.orm import Session
from datetime import timedelta, datetime

from database import Subscription


def extend_subscription(session: Session, telegram_id: int) -> Subscription:
    # Ищем существующую подписку пользователя
    existing_subscription = (
        session.query(Subscription)
        .filter(Subscription.user_id == telegram_id)
        .first()
    )

    if existing_subscription:
        # Продлеваем подписку на 10 дней
        existing_subscription.expiration_date += timedelta(days=10)
        session.commit()
        session.refresh(existing_subscription)
        return existing_subscription
    else:
        # Если подписки нет, создаем новую на 10 дней
        new_subscription = Subscription(
            user_id=telegram_id,
            expiration_date=datetime.utcnow() + timedelta(days=10),
            chat_id="example_chat_id",  # Укажите реальный chat_id, если нужно
        )
        session.add(new_subscription)
        session.commit()
        session.refresh(new_subscription)
        return new_subscription
