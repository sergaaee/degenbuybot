import asyncio
from datetime import datetime

import os

from aiogram import Router

from api_calls import get_ton_balance, get_usdt_bnb_balance, get_bnb_balance, get_base_usdc_balance, \
    get_base_eth_balance, get_usdt_trx_balance, get_trx_balance
from crud.subscriptions import extend_subscription, create_subscription
from crud.transactions import get_transaction_by_telegram_id, create_transaction
from crud.users import get_user_by_telegram_id
from aiogram import F
from aiogram.types import CallbackQuery
from keyboards import (
    get_check_payment_keyboard, get_currency_selection_keyboard,

)
from main import bot, session
from dotenv import load_dotenv

from constants import *

load_dotenv()
sol_wallet_address = os.environ.get("SOL_WALLET_ADDRESS")
usdt_sol_mint_address = os.environ.get("USDT_SOL_MINT_ADDRESS")
ton_wallet_address = os.environ.get("TON_WALLET_ADDRESS")
bsc_wallet_address = os.environ.get("BSC_WALLET_ADDRESS")
tron_wallet_address = os.environ.get("TRON_WALLET_ADDRESS")

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
    base_prices = BASE_PRICES

    amount = base_prices.get(period, 0) / 2 if not is_with_chat else base_prices.get(period, 0)

    subscription_type = "С чатом" if is_with_chat else "Без чата"

    # Создаём транзакцию
    create_transaction(
        session=session,
        telegram_id=user_id,
        blockchain="",  # Укажите конкретную блокчейн-сеть
        expected_amount=amount,
        currency="",  # Валюта будет выбрана позже
        with_chat=is_with_chat,
        period=period,
    )

    await callback.message.edit_text(
        f"Вы выбрали подписку '{subscription_type}' на {period}. Стоимость: USD{amount}.\nВыберите валюту для оплаты.",
        reply_markup=get_currency_selection_keyboard()
    )


@payments_router.callback_query(F.data == "pay_in_SOL")
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


@payments_router.callback_query(F.data == "pay_in_TON")
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


@payments_router.callback_query(F.data == "pay_in_USDT_SOL")
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


@payments_router.callback_query(F.data == "pay_in_BNB")
async def pay_in_bnb_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_bnb_balance, get_bnb_usd_rate

    bnb_usd_rate = get_bnb_usd_rate()
    if bnb_usd_rate <= 0:
        await callback.message.edit_text("Не удалось получить курс BNB/USD. Попробуйте позже.")
        return

    price_in_usd = transaction.expected_amount
    price_in_bnb = price_in_usd / bnb_usd_rate

    current_balance = get_bnb_balance()
    expected_amount = current_balance + price_in_bnb

    transaction.currency = "BNB"
    transaction.blockchain = "BSC"
    transaction.expected_amount = expected_amount
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.6f} BNB.\n"
        f"Текущий курс: 1 BNB = ${bnb_usd_rate:.2f}\n\n"
        f"Адрес: `{bsc_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@payments_router.callback_query(F.data == "pay_in_USDT_BNB")
async def pay_in_usdt_bnb_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_usdt_bnb_balance

    current_balance = get_usdt_bnb_balance()
    expected_amount = current_balance + transaction.expected_amount

    transaction.currency = "USDT"
    transaction.blockchain = "BSC"
    transaction.expected_amount = expected_amount
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.2f} USDT.\n\nАдрес: `{bsc_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@payments_router.callback_query(F.data == "pay_in_ETH_BASE")
async def pay_in_eth_base_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_base_eth_balance, get_eth_usd_rate

    eth_usd_rate = get_eth_usd_rate()
    if eth_usd_rate <= 0:
        await callback.message.edit_text("Не удалось получить курс ETH/USD. Попробуйте позже.")
        return

    price_in_usd = transaction.expected_amount
    price_in_eth = price_in_usd / eth_usd_rate

    current_balance = get_base_eth_balance()
    expected_amount = current_balance + price_in_eth

    transaction.currency = "ETH"
    transaction.blockchain = "Base"
    transaction.expected_amount = expected_amount
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.6f} ETH.\n"
        f"Текущий курс: 1 ETH = ${eth_usd_rate:.2f}\n\n"
        f"Адрес: `{os.environ.get('BASE_WALLET_ADDRESS')}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@payments_router.callback_query(F.data == "pay_in_USDC_BASE")
async def pay_in_usdc_base_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_base_usdc_balance

    current_balance = get_base_usdc_balance()
    expected_amount = current_balance + transaction.expected_amount

    transaction.currency = "USDC"
    transaction.blockchain = "Base"
    transaction.expected_amount = expected_amount
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.2f} USDC.\n\nАдрес: `{os.environ.get('BASE_WALLET_ADDRESS')}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@payments_router.callback_query(F.data == "pay_in_TRX")
async def pay_in_trx_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_trx_balance, get_trx_usd_rate

    trx_usd_rate = get_trx_usd_rate()
    if trx_usd_rate <= 0:
        await callback.message.edit_text("Не удалось получить курс TRX/USD. Попробуйте позже.")
        return

    price_in_usd = transaction.expected_amount
    price_in_trx = price_in_usd / trx_usd_rate

    current_balance = get_trx_balance()
    expected_amount = current_balance + price_in_trx

    transaction.currency = "TRX"
    transaction.blockchain = "TRON"
    transaction.expected_amount = expected_amount
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.6f} TRX.\n"
        f"Текущий курс: 1 TRX = ${trx_usd_rate:.2f}\n\n"
        f"Адрес: `{tron_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@payments_router.callback_query(F.data == "pay_in_USDT_TRON")
async def pay_in_usdt_tron_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.currency:
        await callback.message.edit_text("Активная транзакция не найдена или уже выбрана валюта.")
        return

    from api_calls import get_usdt_trx_balance

    current_balance = get_usdt_trx_balance()
    expected_amount = current_balance + transaction.expected_amount

    transaction.currency = "USDT"
    transaction.blockchain = "TRON"
    transaction.expected_amount = expected_amount
    session.commit()

    await callback.message.edit_text(
        f"Пополните кошелек минимум на {expected_amount - current_balance:.2f} USDT.\n\nАдрес: `{tron_wallet_address}`",
        reply_markup=get_check_payment_keyboard(cancel_button=True),
        parse_mode="Markdown"
    )


@payments_router.callback_query(F.data == "check_payment")
async def check_payment_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    transaction = get_transaction_by_telegram_id(session, user_id)

    if not transaction or transaction.status != "Pending":
        await callback.message.edit_text("Не найдена активная транзакция для проверки.")
        return

    from api_calls import get_sol_balance, get_sol_token_balances
    if transaction.currency == "SOL":
        current_balance = get_sol_balance()
    elif transaction.blockchain == "Solana" and transaction.currency == "USDT":
        token_balances = get_sol_token_balances()
        current_balance = token_balances.get(usdt_sol_mint_address, 0)
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

    if current_balance >= transaction.expected_amount:
        user = get_user_by_telegram_id(session, user_id)

        # Если у пользователя есть пригласивший, продлеваем подписку пригласившему
        if user.invited_by:
            updated_subscription = extend_subscription(session, user.invited_by)
            await bot.send_message(chat_id=user.invited_by, text="Ваша подписка была продлена благодаря рефералу!")

        # Обновляем статус транзакции
        transaction.status = "Success"
        session.commit()

        # Определяем тип подписки
        subscription_type = "Без чата" if not transaction.with_chat else "С чатом"  # Пример определения

        # Создаем подписку
        subscription = create_subscription(session, user_id, subscription_type)

        try:
            await bot.unban_chat_member(CHAT_ID, user_id)
        except Exception:
            pass

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
