from sqlalchemy.orm import Session
from database import Transaction
import random

def get_transaction_by_telegram_id(session: Session, telegram_id: int) -> Transaction | None:
    return session.query(Transaction).filter_by(initiator=telegram_id).first()

def create_transaction(session, telegram_id, base_price, blockchain, currency, period, with_chat):
    """
    Создает транзакцию с плавающей суммой.
    """
    # Уникальная поправка: ±0.01% от base_price
    adjustment = random.uniform(-0.0001, 0.0001) * base_price
    expected_amount = round(base_price + adjustment, 6)  # Уточняем до 6 знаков после запятой

    new_transaction = Transaction(
        initiator=telegram_id,
        blockchain=blockchain,
        expected_amount=expected_amount,
        currency=currency,
        period=period,
        with_chat=with_chat,
        status="Pending"
    )
    session.add(new_transaction)
    session.commit()
    return new_transaction
