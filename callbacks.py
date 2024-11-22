from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER
from aiogram.types import Message, ChatMemberUpdated, ChatPermissions

import strings

from crud.subscriptions import is_user_muted
from crud.users import get_user_by_telegram_id, create_user
from aiogram import F
from aiogram.types import CallbackQuery
from keyboards import (
    get_main_inline_keyboard,
    get_with_chat_inline_keyboard,
    get_without_chat_inline_keyboard,
    get_back_to_main_menu_keyboard,
)
from main import bot, session
from dotenv import load_dotenv

load_dotenv()

router = Router()  # Создаем роутер для всех обработчиков


@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> MEMBER
    )
)
async def on_user_joined(update: ChatMemberUpdated):
    user_id = update.from_user.id
    chat_id = update.chat.id

    if update.new_chat_member.status == "member":  # Пользователь только что присоединился
        # Проверяем, есть ли подписка "Без чата"
        if is_user_muted(session, user_id):
            # Выдаем мут пользователю
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                )
            )


@router.message(CommandStart())
async def command_start_handler(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    # Извлекаем аргументы команды /start
    text_parts = message.text.split()
    args = text_parts[1] if len(text_parts) > 1 else None

    # Проверяем, есть ли пользователь в базе
    user = get_user_by_telegram_id(session, telegram_id)

    if not user:
        # Если есть аргументы, записываем, кто пригласил
        invited_by = int(args) if args and args.isdigit() else None
        if not create_user(session, telegram_id, username, invited_by):
            await message.answer("Попытка не пытка")

    await message.answer(
        strings.formatted_welcome,
        reply_markup=get_main_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите вариант:",
        reply_markup=get_main_inline_keyboard(),
    )


@router.message(Command("referral"))
async def referral_command_handler(message: Message):
    telegram_id = message.from_user.id
    bot_username = (await bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={telegram_id}"

    formatted_referral = strings.referral_template.format(referral_link=referral_link)

    await message.answer(
        formatted_referral,
        reply_markup=get_back_to_main_menu_keyboard(),
        parse_mode=ParseMode.HTML  # Указываем использование HTML
    )


@router.callback_query(F.data == "referral_code")
async def referral_command_callback_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    bot_username = (await bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={telegram_id}"

    formatted_referral = strings.referral_template.format(referral_link=referral_link)

    await callback.message.answer(
        formatted_referral,
        reply_markup=get_back_to_main_menu_keyboard(),
        parse_mode=ParseMode.HTML  # Указываем использование HTML
    )
