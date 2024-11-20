from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_inline_keyboard():
    """
    Основная inline-клавиатура с кнопками 'С чатом' и 'Без чата'.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="С чатом", callback_data="with_chat")
    #builder.button(text="Без чата", callback_data="without_chat")
    builder.adjust(1)  # Кнопки в один ряд
    return builder.as_markup()


def get_with_chat_inline_keyboard():
    """
    Inline-клавиатура для выбора тарифа 'С чатом'.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="1W=5$", callback_data="with_chat_1w")
    builder.button(text="1M=100$", callback_data="with_chat_1m")
    builder.button(text="3M=400$", callback_data="with_chat_3m")
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_without_chat_inline_keyboard():
    """
    Inline-клавиатура для выбора тарифа 'Без чата'.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="1W=10$", callback_data="without_chat_1w")
    builder.button(text="1M=50$", callback_data="without_chat_1m")
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
    builder.button(text="Оплатить в SOL", callback_data="pay_in_SOL")
    builder.button(text="Оплатить в USDT SOL", callback_data="pay_in_USDT_SOL")
    builder.button(text="Оплатить в TON", callback_data="pay_in_TON")
    return builder.as_markup()


