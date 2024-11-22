from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()


# Модель Users
class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    reg_date = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(Integer, nullable=True)


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    initiator = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    blockchain = Column(String, nullable=False)
    expected_amount = Column(Integer, nullable=False)  # Ожидаемый баланс
    currency = Column(String, nullable=False)  # SOL или USDT
    status = Column(String, default="Pending")  # Pending, Success, или Failed
    created_at = Column(DateTime, default=datetime.utcnow)
    period = Column(String, nullable=True)
    referral_code = Column(String, nullable=True)
    with_chat = Column(Boolean, nullable=False, default=False)
    tx_id = Column(String, unique=True, nullable=True)
    wallet_address = Column(String, nullable=True)


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    chat_id = Column(String, nullable=False)  # ID чата, куда добавляется пользователь
    muted = Column(Boolean, nullable=False, default=False)


# Инициализация базы данных
def init_db(db_path='sqlite:///database.db'):
    engine = create_engine(db_path, echo=True)
    Base.metadata.create_all(engine)
    print("База данных создана или уже существует.")
    return sessionmaker(bind=engine)
