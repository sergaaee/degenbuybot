from sqlalchemy.orm import Session
from database import User


def get_user_by_telegram_id(session: Session, telegram_id: int) -> User | None:
    return session.query(User).filter_by(telegram_id=telegram_id).first()


def create_user(session, telegram_id, username=None, invited_by=None):
    if telegram_id == invited_by:
        return False
    new_user = User(
        telegram_id=telegram_id,
        username=username,
        invited_by=invited_by
    )
    session.add(new_user)
    session.commit()
    return True
