import asyncio
from datetime import datetime, timedelta

import os

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration

from api_calls import get_ton_balance
from crud.transactions import get_transaction_by_telegram_id, create_transaction
from crud.users import get_user_by_telegram_id, create_user
from database import Subscription
from aiogram import F
from aiogram.types import CallbackQuery
from keyboards import (
    get_main_inline_keyboard,
    get_with_chat_inline_keyboard,
    get_without_chat_inline_keyboard, get_check_payment_keyboard, get_currency_selection_keyboard,
)
from main import bot, session
from dotenv import load_dotenv

load_dotenv()
sol_wallet_address = os.environ.get("SOL_WALLET_ADDRESS")
usdt_sol_mint_address = os.environ.get("USDT_SOL_MINT_ADDRESS")
ton_wallet_address = os.environ.get("TON_WALLET_ADDRESS")

router = Router()  # Создаем роутер для всех обработчиков


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, есть ли пользователь в базе
    user = get_user_by_telegram_id(session, telegram_id)

    if not user:
        create_user(session, telegram_id, username)
    await message.answer(
        f"Привет, {html_decoration.bold(message.from_user.full_name)}! Выбери один из вариантов:",
        reply_markup=get_main_inline_keyboard()
    )


@router.callback_query(F.data == "with_chat")
async def with_chat_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите период:",
        reply_markup=get_with_chat_inline_keyboard(),
    )


@router.callback_query(F.data == "without_chat")
async def without_chat_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите период:",
        reply_markup=get_without_chat_inline_keyboard(),
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите вариант:",
        reply_markup=get_main_inline_keyboard(),
    )


@router.callback_query(F.data.startswith("with_chat_") | F.data.startswith("without_chat_"))
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

    period = callback.data.split("_")[-1]  # Например, "1w", "1m", "3m"
    period_prices = {
        "1w": 1,
        "1m": 100,
        "3m": 400
    }
    amount = period_prices.get(period, 0)  # Цена в USD

    # Создаем транзакцию с указанием blockchain
    create_transaction(
        session=session,
        telegram_id=user_id,
        blockchain="",  # Укажите конкретную блокчейн-сеть
        expected_amount=amount,
        currency="",  # Валюта будет выбрана позже
        period=period,
    )

    await callback.message.edit_text(
        f"Вы выбрали тариф на {period}. Выберите валюту для оплаты.",
        reply_markup=get_currency_selection_keyboard()
    )


@router.callback_query(F.data == "pay_in_SOL")
async def pay_in_sol_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_sol_balance, get_sol_usd_rate

    # Получаем текущий курс SOL/USD
    sol_usd_rate = get_sol_usd_rate()
    if sol_usd_rate <= 0:
        await callback.message.edit_text("Не удалось получить курс SOL/USD. Попробуйте позже.")
        return

    # Конвертируем цену подписки в SOL
    price_in_usd = transaction.expected_amount  # Стоимость подписки в USD
    price_in_sol = price_in_usd / sol_usd_rate  # Конвертируем в SOL

    # Получаем текущий баланс кошелька
    current_balance = get_sol_balance()
    expected_amount = current_balance + price_in_sol  # Баланс + стоимость в SOL

    # Обновляем транзакцию
    transaction.currency = "SOL"
    transaction.blockchain = "Solana"
    transaction.expected_amount = expected_amount  # Ожидаемая сумма в SOL
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.6f} SOL.\n"
        f"Текущий курс: 1 SOL = ${sol_usd_rate:.2f}\n\n"
        f"Адрес: `{sol_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "pay_in_TON")
async def pay_in_ton_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_ton_balance, get_ton_usd_rate

    # Получаем текущий курс SOL/USD
    ton_usd_rate = get_ton_usd_rate()
    if ton_usd_rate <= 0:
        await callback.message.edit_text("Не удалось получить курс TON/USD. Попробуйте позже.")
        return

    # Конвертируем цену подписки в ton
    price_in_usd = transaction.expected_amount  # Стоимость подписки в USD
    price_in_ton = price_in_usd / ton_usd_rate  # Конвертируем в ton

    # Получаем текущий баланс кошелька
    current_balance = get_ton_balance()
    expected_amount = current_balance + price_in_ton  # Баланс + стоимость в ton

    # Обновляем транзакцию
    transaction.currency = "TON"
    transaction.blockchain = "TON"
    transaction.expected_amount = expected_amount  # Ожидаемая сумма в ton
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.6f} TON.\n"
        f"Текущий курс: 1 TON = ${ton_usd_rate:.2f}\n\n"
        f"Адрес: `{ton_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "pay_in_USDT_SOL")
async def pay_in_usdt_sol_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_sol_token_balances

    token_balances = get_sol_token_balances()
    current_balance = token_balances.get(usdt_sol_mint_address, 0)
    expected_amount = current_balance + transaction.expected_amount  # Баланс + стоимость тарифа

    transaction.currency = "USDT"
    transaction.blockchain = "Solana"
    transaction.expected_amount = expected_amount  # Обновляем ожидаемую сумму
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.2f} USDT.\n\nАдрес: `{sol_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "cancel_payment")
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
        await callback.message.edit_text("Транзакция отменена.")
    else:
        await callback.message.edit_text("Активная транзакция не найдена.")


@router.callback_query(F.data == "check_payment")
async def check_payment_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.status != "Pending":
        await callback.message.edit_text("Не найдена активная транзакция для проверки.")
        return


    from api_calls import get_sol_balance, get_sol_token_balances
    if transaction.currency == "SOL":
        current_balance = get_sol_balance()
    elif transaction.currency == "USDT":
        token_balances = get_sol_token_balances()
        current_balance = token_balances.get(usdt_sol_mint_address, 0)
    elif transaction.currency == "TON":
        current_balance = get_ton_balance()

    if current_balance >= transaction.expected_amount:
        # Обновляем статус транзакции
        transaction.status = "Success"
        session.commit()

        # Создаем одноразовую ссылку
        chat_id = "-1002225835813"  # Заглушка
        invite_link = await bot.create_chat_invite_link(chat_id, expire_date=None, member_limit=1)

        # Отправляем пользователю одноразовую ссылку
        await callback.message.edit_text(
            f"Оплата успешно выполнена! Вот ваша одноразовая ссылка на чат:\n\n{invite_link.invite_link}"
        )

        # Добавляем запись в таблицу Subscriptions
        period = {
            "1w": 7,
            "1m": 30,
            "3m": 180,
        }

        delta = period.get(transaction.period, 0)

        if delta == 0:
            await callback.message.edit_text(
                "Оплата прошла успешно, но с выдачей доступа что-то пошло не так, пожалуйста, свяжитесь с @d10658")
            return

        expiration_date = datetime.utcnow() + timedelta(days=delta)
        subscription = Subscription(user_id=user_id, expiration_date=expiration_date, chat_id=chat_id)
        session.add(subscription)
        session.commit()
    else:
        temp_message = await callback.message.answer("Оплата пока не поступила. Попробуйте позже.")
        await asyncio.sleep(5)
        await temp_message.delete()
