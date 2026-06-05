from __future__ import annotations

from typing import Iterable, Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.config import settings
from bot.database.models import Category, Mockup, Subcategory
from bot.keyboards.callbacks import (
    AgreeCb,
    CategoryCb,
    MockupCb,
    NavCb,
    SubcategoryCb,
)


def kb_webapp() -> ReplyKeyboardMarkup:
    """Reply-клавиатура с кнопкой открытия Mini App."""
    kb = ReplyKeyboardBuilder()
    kb.button(
        text="🚀 Открыть каталог",
        web_app=WebAppInfo(url=settings.webapp_url),
    )
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def kb_open_app() -> InlineKeyboardMarkup:
    """Inline-кнопка для прямого открытия Mini App под приветствием."""
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🚀 Открыть приложение",
        web_app=WebAppInfo(url=settings.webapp_url),
    )
    kb.adjust(1)
    return kb.as_markup()


def kb_agreement() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📜 Прочитать соглашение", callback_data=NavCb(to="agreement").pack())
    kb.button(text="✅ Принимаю", callback_data=AgreeCb().pack())
    kb.adjust(1)
    return kb.as_markup()


def kb_agreement_full() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Принимаю", callback_data=AgreeCb().pack())
    kb.adjust(1)
    return kb.as_markup()


def kb_main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎨 Каталог макетов", callback_data=NavCb(to="browse").pack())
    kb.button(text="❤️ Мои избранные", callback_data=NavCb(to="likes").pack())
    kb.button(text="💬 Связаться с менеджером", callback_data=NavCb(to="contact").pack())
    kb.button(text="📜 Соглашение", callback_data=NavCb(to="agreement").pack())
    kb.button(text="❓ Помощь", callback_data=NavCb(to="help").pack())
    kb.adjust(1, 1, 1, 2)
    return kb.as_markup()


def kb_categories(categories: Iterable[Category]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat.display, callback_data=CategoryCb(id=cat.id).pack())
    kb.button(text="🏠 В меню", callback_data=NavCb(to="menu").pack())
    # 1 кнопка в строке для категорий (длинные имена), кроме последней
    items = list(categories)
    rows = [1] * len(items) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


def kb_subcategories(
    subs: Iterable[Subcategory], category_id: int
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for sub in subs:
        kb.button(text=sub.name, callback_data=SubcategoryCb(id=sub.id).pack())
    kb.button(text="⬅️ К категориям", callback_data=NavCb(to="browse").pack())
    kb.button(text="🏠 В меню", callback_data=NavCb(to="menu").pack())
    items = list(subs)
    rows = [2] * (len(items) // 2)
    if len(items) % 2:
        rows.append(1)
    rows.append(2)  # навигационные
    kb.adjust(*rows)
    return kb.as_markup()


def kb_mockup_view(
    mockup: Mockup,
    *,
    is_liked: bool,
    has_prev: bool,
    has_next: bool,
    category_id: int,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    like_text = "💔 Убрать из избранного" if is_liked else "❤️ В избранное"
    kb.button(
        text=like_text,
        callback_data=MockupCb(id=mockup.id, action="like").pack(),
    )
    if mockup.figma_link:
        kb.button(text="🔗 Открыть в Figma", url=mockup.figma_link)
    kb.button(
        text="💬 Хочу этот сайт",
        callback_data=MockupCb(id=mockup.id, action="contact").pack(),
    )

    nav_buttons = []
    if has_prev:
        nav_buttons.append(("⬅️", MockupCb(id=mockup.id, action="prev").pack()))
    if has_next:
        nav_buttons.append(("➡️", MockupCb(id=mockup.id, action="next").pack()))
    for text, cb in nav_buttons:
        kb.button(text=text, callback_data=cb)

    kb.button(
        text="📁 К списку",
        callback_data=NavCb(to="back_to_subs", id=category_id).pack(),
    )
    kb.button(text="🏠 В меню", callback_data=NavCb(to="menu").pack())

    rows = [1]
    if mockup.figma_link:
        rows.append(1)
    rows.append(1)  # contact
    if nav_buttons:
        rows.append(len(nav_buttons))
    rows.append(2)  # back to list + menu
    kb.adjust(*rows)
    return kb.as_markup()


def kb_back_to_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 В меню", callback_data=NavCb(to="menu").pack())
    return kb.as_markup()


def kb_contact_manager(manager_username: Optional[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if manager_username:
        url = f"https://t.me/{manager_username.lstrip('@')}"
        kb.button(text="✍️ Написать менеджеру", url=url)
    kb.button(text="🏠 В меню", callback_data=NavCb(to="menu").pack())
    kb.adjust(1)
    return kb.as_markup()
