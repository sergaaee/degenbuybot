import asyncio
from datetime import datetime

import os

from aiogram import Router

from api_calls import get_ton_balance, get_usdt_bnb_balance, get_bnb_balance, get_base_usdc_balance, \
    get_base_eth_balance, get_usdt_trx_balance, get_trx_balance, get_sol_balance, get_sol_usd_rate, get_ton_usd_rate, \
    get_bnb_usd_rate, get_eth_usd_rate, get_trx_usd_rate
from crud.subscriptions import extend_subscription, create_subscription
from crud.transactions import get_transaction_by_telegram_id, create_transaction
from crud.users import get_user_by_telegram_id
from aiogram import F
from aiogram.types import CallbackQuery
from keyboards import (
    get_check_payment_keyboard, get_currency_selection_keyboard, get_with_chat_inline_keyboard,
    get_without_chat_inline_keyboard,

)
from main import bot, session
from dotenv import load_dotenv
from new_api_calls import validate_payment

from constants import *

load_dotenv()

CURRENCY_HANDLERS = {
    "SOL": ("SOL", "SOL", lambda: get_sol_balance(), get_sol_usd_rate),
    "TON": ("TON", "TON", lambda: get_ton_balance(), get_ton_usd_rate),
    "BNB": ("BSC", "BNB", lambda: get_bnb_balance(), get_bnb_usd_rate),
    "USDTSOL": ("SOL", "USDT", lambda: get_sol_balance(), lambda: 1),
    "USDTBNB": ("BSC", "USDT", lambda: get_usdt_bnb_balance(), lambda: 1),
    "ETHBASE": ("Base", "ETH", lambda: get_base_eth_balance(), get_eth_usd_rate),
    "USDCBASE": ("Base", "USDC", lambda: get_base_usdc_balance(), lambda: 1),
    "TRX": ("TRON", "TRX", lambda: get_trx_balance(), get_trx_usd_rate),
    "USDTTRON": ("TRON", "USDT", lambda: get_usdt_trx_balance(), lambda: 1),
}

payments_router = Router()  # Создаем роутер для всех обработчиков


@payments_router.callback_query(F.data.startswith("with_chat_") | F.data.startswith("without_chat_"))
async def tariff_callback(callback: CallbackQuery) -> None:
    """
    Обработчик выбора тарифа.
    """
    user_id = callback.from_user.id
    existing_transaction = get_transaction_by_telegram_id(session, user_id)

    if existing_transaction and existing_transaction.status == "Pending" and \
            (datetime.utcnow() - existing_transaction.created_at).total_seconds() < 15 * 60:
        await callback.message.edit_text(
            f"У вас уже есть активная транзакция. Проверьте оплату или отмените ее.",
            reply_markup=get_check_payment_keyboard(cancel_button=True)
        )
        return

    # Определяем тип подписки и период
    is_with_chat = callback.data.startswith("with_chat_")
    period = callback.data.split("_")[-1]  # Например, "1w", "1m", "3m"

    # Определяем цену
    base_prices = {
        "1m": 50,  # Базовая цена "С чатом" за месяц
        "3m": 130,  # Базовая цена "С чатом" за три месяца
        "6m": 250,
        "1y": 490,
        "lt": 1500,
    }
    amount = base_prices.get(period, 0) / 2 if not is_with_chat else base_prices.get(period, 0)

    subscription_type = "С чатом" if is_with_chat else "Без чата"

    # Создаём транзакцию
    create_transaction(
        session=session,
        telegram_id=user_id,
        blockchain="",  # Укажите конкретную блокчейн-сеть
        base_price=amount,
        currency="",  # Валюта будет выбрана позже
        with_chat=is_with_chat,
        period=period,
    )

    await callback.message.edit_text(
        f"Вы выбрали подписку '{subscription_type}' на {period}. Стоимость: USD{amount}.\nВыберите валюту для оплаты.",
        reply_markup=get_currency_selection_keyboard()
    )


@payments_router.callback_query(F.data == "with_chat")
async def with_chat_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите период:",
        reply_markup=get_with_chat_inline_keyboard(),
    )


@payments_router.callback_query(F.data == "without_chat")
async def without_chat_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите период:",
        reply_markup=get_without_chat_inline_keyboard(),
    )


def calculate_expected_amount(transaction, balance_func, rate_func):
    rate = rate_func()
    if rate <= 0:
        raise ValueError("Не удалось получить курс валюты.")

    price_in_usd = transaction.expected_amount
    price_in_currency = price_in_usd / rate

    current_balance = balance_func()
    expected_amount = current_balance + price_in_currency

    return expected_amount, rate


def update_transaction(session, transaction, blockchain, currency, expected_amount, wallet_address):
    transaction.blockchain = blockchain
    transaction.currency = currency
    transaction.wallet_address = wallet_address
    transaction.expected_amount = expected_amount
    session.commit()


async def send_payment_instruction(callback, transaction, wallet_address):
    """
    Отправка пользователю инструкции по оплате.
    """
    await callback.message.edit_text(
        f"Для завершения оплаты, отправьте точную сумму: {transaction.expected_amount:.6f} {transaction.currency}\n"
        f"на адрес:\n\n"
        f"`{wallet_address}`\n\n"
        f"Убедитесь, что сумма указана точно, иначе платеж не будет подтвержден.",
        parse_mode="Markdown",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
    )


@payments_router.callback_query(F.data.startswith("pay_in_"))
async def handle_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    currency_key = callback.data.split("_")[-1]
    print(currency_key)
    handler = CURRENCY_HANDLERS.get(currency_key)

    if not handler:
        await callback.message.edit_text("Неизвестная валюта.")
        return

    blockchain, currency, balance_func, rate_func = handler

    try:
        expected_amount, rate = calculate_expected_amount(transaction, balance_func, rate_func)
    except ValueError as e:
        await callback.message.edit_text(str(e))
        return

    wallet_address = os.environ.get(f"{blockchain.upper()}_WALLET_ADDRESS")
    update_transaction(session, transaction, blockchain, currency, expected_amount, wallet_address)

    await send_payment_instruction(
        callback, transaction, wallet_address
    )


@payments_router.callback_query(F.data == "cancel_payment")
async def cancel_payment_callback(callback: CallbackQuery) -> None:
    """
    Обработка отмены платежа.
    """
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if transaction and transaction.status == "Pending":
        # Удаляем транзакцию из базы
        session.delete(transaction)
        session.commit()
        await callback.message.edit_text("Оплата отменена.")
    else:
        await callback.message.edit_text("Активная заявка на оплату не найдена.")


@payments_router.callback_query(F.data == "check_payment")
async def check_payment_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.status != "Pending":
        await callback.message.edit_text("Не найдена активная транзакция для проверки.")
        return

    from api_calls import get_sol_balance, get_sol_usdt_balance
    if transaction.currency == "SOL":
        current_balance = get_sol_balance()
    elif transaction.blockchain == "SOL" and transaction.currency == "USDT":
        current_balance = get_sol_usdt_balance()
    elif transaction.currency == "TON":
        current_balance = get_ton_balance()
    elif transaction.blockchain == "BSC" and transaction.currency == "USDT":
        current_balance = get_usdt_bnb_balance()
    elif transaction.blockchain == "BSC" and transaction.currency == "BNB":
        current_balance = get_bnb_balance()
    elif transaction.blockchain == "Base" and transaction.currency == "USDC":
        current_balance = get_base_usdc_balance()
    elif transaction.blockchain == "Base" and transaction.currency == "ETH":
        current_balance = get_base_eth_balance()
    elif transaction.blockchain == "TRON" and transaction.currency == "USDT":
        current_balance = get_usdt_trx_balance()
    elif transaction.blockchain == "TRON" and transaction.currency == "TRX":
        current_balance = get_trx_balance()

    print(validate_payment(transaction))

    if current_balance >= transaction.expected_amount - transaction.expected_amount * 0.01:
        user = get_user_by_telegram_id(session, user_id)

        # Если у пользователя есть пригласивший, продлеваем подписку пригласившему
        if user.invited_by:
            extend_subscription(session, user.invited_by)
            await bot.send_message(chat_id=user.invited_by, text="Ваша подписка была продлена благодаря рефералу!")

        # Обновляем статус транзакции
        transaction.status = "Success"
        session.commit()

        # Определяем тип подписки
        subscription_type = "Без чата" if not transaction.with_chat else "С чатом"

        # Создаем подписку
        subscription = create_subscription(session, user_id, subscription_type)

        # Отправляем ссылку на чат, если подписка "С чатом"
        invite_link = await bot.create_chat_invite_link(CHAT_ID, expire_date=None, member_limit=1)
        if subscription_type == "С чатом":
            await callback.message.edit_text(
                f"Оплата успешно выполнена! Вот ваша одноразовая ссылка на чат:\n\n{invite_link.invite_link}"
            )
        else:
            await callback.message.edit_text(
                f"Оплата успешно выполнена! Ваша подписка без возможности писать активирована до {subscription.expiration_date.strftime('%Y-%m-%d')}."
                f"\n\nСсылка: {invite_link.invite_link}"
            )
    else:
        temp_message = await callback.message.answer("Оплата еще не поступила, попробуйте позже.")
        await asyncio.sleep(5)
        await temp_message.delete()
