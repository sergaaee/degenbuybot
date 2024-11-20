from sqlalchemy.orm import Session
from database import User

def get_user_by_telegram_id(session: Session, telegram_id: int) -> User | None:
    return session.query(User).filter_by(telegram_id=telegram_id).first()

def create_user(session: Session, telegram_id: int, username: str) -> User:
    new_user = User(telegram_id=telegram_id, username=username)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)  # Обновляет объект из базы
    return new_user
