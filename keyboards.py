from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_inline_keyboard():
    """
    Основная inline-клавиатура с кнопками 'С чатом' и 'Без чата'.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="С чатом", callback_data="with_chat")
    builder.button(text="Без чата", callback_data="without_chat")
    builder.button(text="Реферальный код", callback_data="referral_code")
    builder.adjust(1)  # Кнопки в один ряд
    return builder.as_markup()


def get_with_chat_inline_keyboard():
    """
    Inline-клавиатура для выбора тарифа 'С чатом'.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="1M=50$", callback_data="with_chat_1w")
    builder.button(text="3M=130$", callback_data="with_chat_1m")
    builder.button(text="6M=250$", callback_data="with_chat_3m")
    builder.button(text="1Y=490$", callback_data="with_chat_1y")
    builder.button(text="Навсегда=1500$", callback_data="with_chat_lt")
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_without_chat_inline_keyboard():
    """
    Inline-клавиатура для выбора тарифа 'Без чата'.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="1M=25$", callback_data="without_chat_1w")
    builder.button(text="3M=65$", callback_data="without_chat_1m")
    builder.button(text="6M=125$", callback_data="without_chat_3m")
    builder.button(text="1Y=245$", callback_data="without_chat_1y")
    builder.button(text="Навсегда=750$", callback_data="without_chat_lt")
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def get_check_payment_keyboard(cancel_button=False):
    builder = InlineKeyboardBuilder()
    builder.button(text="Проверить оплату", callback_data="check_payment")
    if cancel_button:
        builder.button(text="Отмена", callback_data="cancel_payment")
    return builder.as_markup()

def get_currency_selection_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="SOL", callback_data="pay_in_SOL")
    builder.button(text="USDT SOL", callback_data="pay_in_USDT_SOL")
    builder.button(text="BNB", callback_data="pay_in_BNB")
    builder.button(text="USDT BNB", callback_data="pay_in_USDT_BNB")
    builder.button(text="ETH (Base)", callback_data="pay_in_ETH_BASE")
    builder.button(text="USDC (Base)", callback_data="pay_in_USDC_BASE")
    builder.button(text="TRX (TRON)", callback_data="pay_in_TRX")
    builder.button(text="USDT (TRON)", callback_data="pay_in_USDT_TRON")
    builder.button(text="TON", callback_data="pay_in_TON")
    builder.adjust(2)
    return builder.as_markup()


