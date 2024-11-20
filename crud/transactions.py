from sqlalchemy.orm import Session
from database import Transaction

def get_transaction_by_telegram_id(session: Session, telegram_id: int) -> Transaction | None:
    return session.query(Transaction).filter_by(initiator=telegram_id).first()

def create_transaction(session: Session, telegram_id: int, blockchain: str, expected_amount: float, currency: str, period: str, with_chat: bool) -> Transaction:
    new_transaction = Transaction(
        initiator=telegram_id,
        blockchain=blockchain,  # Здесь может быть None
        expected_amount=expected_amount,
        with_chat=with_chat,
        currency=currency,
        status="Pending",
        period=period,
    )
    session.add(new_transaction)
    session.commit()
    session.refresh(new_transaction)
    return new_transaction



