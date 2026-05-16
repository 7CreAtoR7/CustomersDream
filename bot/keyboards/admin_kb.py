from __future__ import annotations

from typing import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import Category, ContactRequest, Mockup, Subcategory
from bot.keyboards.callbacks import AdminCb


def kb_admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📂 Категории", callback_data=AdminCb(action="cats").pack())
    kb.button(text="➕ Категория", callback_data=AdminCb(action="add_cat").pack())
    kb.button(text="➕ Подкатегория", callback_data=AdminCb(action="add_sub").pack())
    kb.button(text="➕ Макет", callback_data=AdminCb(action="add_mockup").pack())
    kb.button(text="📨 Заявки", callback_data=AdminCb(action="leads").pack())
    kb.button(text="📊 Статистика", callback_data=AdminCb(action="stats").pack())
    kb.adjust(1, 1, 1, 1, 2)
    return kb.as_markup()


def kb_cancel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data=AdminCb(action="cancel").pack())
    return kb.as_markup()


def kb_skip_or_cancel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭ Пропустить", callback_data=AdminCb(action="skip").pack())
    kb.button(text="❌ Отмена", callback_data=AdminCb(action="cancel").pack())
    kb.adjust(2)
    return kb.as_markup()


def kb_pick_category(
    categories: Iterable[Category], action: str
) -> InlineKeyboardMarkup:
    """Выбор категории для добавления подкатегории/макета."""
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat.display, callback_data=AdminCb(action=action, id=cat.id).pack())
    kb.button(text="❌ Отмена", callback_data=AdminCb(action="cancel").pack())
    rows = [1] * len(list(categories)) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


def kb_pick_subcategory(
    subs: Iterable[Subcategory], action: str
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for sub in subs:
        kb.button(text=sub.name, callback_data=AdminCb(action=action, id=sub.id).pack())
    kb.button(text="❌ Отмена", callback_data=AdminCb(action="cancel").pack())
    rows = [1] * len(list(subs)) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


def kb_categories_admin(categories: Iterable[Category]) -> InlineKeyboardMarkup:
    """Список категорий для редактирования/удаления."""
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat.display, callback_data=AdminCb(action="cat_view", id=cat.id).pack())
    kb.button(text="🏠 В админ-меню", callback_data=AdminCb(action="menu").pack())
    rows = [1] * len(list(categories)) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


def kb_category_actions(cat: Category) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="📁 Подкатегории",
        callback_data=AdminCb(action="cat_subs", id=cat.id).pack(),
    )
    kb.button(
        text="🗑 Удалить категорию",
        callback_data=AdminCb(action="del_cat", id=cat.id).pack(),
    )
    kb.button(text="⬅️ Назад", callback_data=AdminCb(action="cats").pack())
    kb.adjust(1, 1, 1)
    return kb.as_markup()


def kb_subs_admin(subs: Iterable[Subcategory], category_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for sub in subs:
        kb.button(
            text=sub.name,
            callback_data=AdminCb(action="sub_view", id=sub.id).pack(),
        )
    kb.button(
        text="⬅️ К категории",
        callback_data=AdminCb(action="cat_view", id=category_id).pack(),
    )
    rows = [1] * len(list(subs)) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


def kb_sub_actions(sub: Subcategory) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🖼 Макеты",
        callback_data=AdminCb(action="sub_mockups", id=sub.id).pack(),
    )
    kb.button(
        text="🗑 Удалить подкатегорию",
        callback_data=AdminCb(action="del_sub", id=sub.id).pack(),
    )
    kb.button(
        text="⬅️ Назад",
        callback_data=AdminCb(action="cat_subs", id=sub.category_id).pack(),
    )
    kb.adjust(1, 1, 1)
    return kb.as_markup()


def kb_mockups_admin(mockups: Iterable[Mockup], sub_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in mockups:
        kb.button(
            text=f"#{m.id} — {m.title}",
            callback_data=AdminCb(action="mockup_view", id=m.id).pack(),
        )
    kb.button(
        text="⬅️ К подкатегории",
        callback_data=AdminCb(action="sub_view", id=sub_id).pack(),
    )
    rows = [1] * len(list(mockups)) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


def kb_mockup_actions(m: Mockup) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🗑 Удалить макет",
        callback_data=AdminCb(action="del_mockup", id=m.id).pack(),
    )
    kb.button(
        text="⬅️ Назад",
        callback_data=AdminCb(action="sub_mockups", id=m.subcategory_id).pack(),
    )
    kb.adjust(1, 1)
    return kb.as_markup()


def kb_lead(req: ContactRequest) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Закрыть заявку",
        callback_data=AdminCb(action="lead_done", id=req.id).pack(),
    )
    kb.button(text="⬅️ К списку", callback_data=AdminCb(action="leads").pack())
    kb.adjust(1, 1)
    return kb.as_markup()


def kb_back_admin() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 В админ-меню", callback_data=AdminCb(action="menu").pack())
    return kb.as_markup()
