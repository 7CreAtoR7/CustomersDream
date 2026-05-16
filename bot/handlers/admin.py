from __future__ import annotations

from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.admin_kb import (
    kb_admin_menu,
    kb_back_admin,
    kb_cancel,
    kb_categories_admin,
    kb_category_actions,
    kb_lead,
    kb_mockup_actions,
    kb_mockups_admin,
    kb_pick_category,
    kb_pick_subcategory,
    kb_skip_or_cancel,
    kb_sub_actions,
    kb_subs_admin,
)
from bot.keyboards.callbacks import AdminCb
from bot.services import crud
from bot.states.admin_states import AddCategory, AddMockup, AddSubcategory
from bot.utils import texts

router = Router(name="admin")


# ---------- Защита: только админы ----------

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not message.from_user or not settings.is_admin(message.from_user.id):
        await message.answer(texts.NOT_ADMIN)
        return
    await state.clear()
    await message.answer(texts.ADMIN_MENU, reply_markup=kb_admin_menu())


@router.callback_query(AdminCb.filter(F.action == "menu"))
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    await state.clear()
    if callback.message:
        try:
            await callback.message.edit_text(
                texts.ADMIN_MENU, reply_markup=kb_admin_menu()
            )
        except Exception:
            await callback.message.answer(
                texts.ADMIN_MENU, reply_markup=kb_admin_menu()
            )
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "cancel"))
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    await state.clear()
    if callback.message:
        try:
            await callback.message.edit_text(
                texts.ADMIN_MENU, reply_markup=kb_admin_menu()
            )
        except Exception:
            await callback.message.answer(
                texts.ADMIN_MENU, reply_markup=kb_admin_menu()
            )
    await callback.answer("Отменено")


# ---------- Список категорий / детали ----------

@router.callback_query(AdminCb.filter(F.action == "cats"))
async def cb_cats(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    cats = await crud.list_categories(session, only_active=False)
    if not cats:
        text = "Категорий пока нет. Добавь первую через «➕ Категория»."
        kb = kb_back_admin()
    else:
        text = "📂 <b>Все категории</b>\n\nНажми, чтобы открыть детали."
        kb = kb_categories_admin(cats)
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "cat_view"))
async def cb_cat_view(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    cat = await crud.get_category(session, callback_data.id)
    if cat is None or not callback.message:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    subs = await crud.list_subcategories(session, cat.id, only_active=False)
    text = (
        f"📁 <b>{cat.display}</b>\n"
        f"ID: <code>{cat.id}</code>\n"
        f"Активна: {'да' if cat.is_active else 'нет'}\n"
        f"Подкатегорий: {len(subs)}\n\n"
        f"{cat.description or ''}"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb_category_actions(cat))
    except Exception:
        await callback.message.answer(text, reply_markup=kb_category_actions(cat))
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "cat_subs"))
async def cb_cat_subs(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    cat = await crud.get_category(session, callback_data.id)
    if cat is None or not callback.message:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    subs = await crud.list_subcategories(session, cat.id, only_active=False)
    text = f"📁 Подкатегории <b>{cat.display}</b>"
    if not subs:
        text += "\n\nПока пусто. Добавь через «➕ Подкатегория»."
        kb = kb_back_admin()
    else:
        kb = kb_subs_admin(subs, cat.id)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "sub_view"))
async def cb_sub_view(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    sub = await crud.get_subcategory(session, callback_data.id)
    if sub is None or not callback.message:
        await callback.answer("Подкатегория не найдена", show_alert=True)
        return
    mockups = await crud.list_mockups(session, sub.id, only_active=False)
    text = (
        f"📁 <b>{sub.name}</b> ({sub.category.display})\n"
        f"ID: <code>{sub.id}</code>\n"
        f"Макетов: {len(mockups)}\n\n"
        f"{sub.description or ''}"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb_sub_actions(sub))
    except Exception:
        await callback.message.answer(text, reply_markup=kb_sub_actions(sub))
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "sub_mockups"))
async def cb_sub_mockups(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    sub = await crud.get_subcategory(session, callback_data.id)
    if sub is None or not callback.message:
        await callback.answer("Подкатегория не найдена", show_alert=True)
        return
    mockups = await crud.list_mockups(session, sub.id, only_active=False)
    text = f"🖼 Макеты <b>{sub.name}</b>"
    if not mockups:
        text += "\n\nМакетов нет. Добавь через «➕ Макет» в админ-меню."
        kb = kb_back_admin()
    else:
        kb = kb_mockups_admin(mockups, sub.id)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "mockup_view"))
async def cb_mockup_view(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, bot: Bot
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    m = await crud.get_mockup(session, callback_data.id)
    if m is None or not callback.message:
        await callback.answer("Макет не найден", show_alert=True)
        return
    sub = m.subcategory
    cat = sub.category if sub else None
    path = f"{cat.display} → {sub.name}" if (cat and sub) else ""
    price = (
        f"{m.price_cents / 100:.2f} {m.currency or settings.default_currency}"
        if m.price_cents
        else "по запросу"
    )
    caption = (
        f"<b>{m.title}</b>\n"
        f"<i>{path}</i>\n"
        f"ID: <code>{m.id}</code>\n"
        f"Активен: {'да' if m.is_active else 'нет'}\n"
        f"Стоимость: {price}\n"
        f"Figma: {m.figma_link or '—'}\n\n"
        f"{m.description or ''}"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass
    if m.photo_file_id:
        await bot.send_photo(
            callback.message.chat.id,
            photo=m.photo_file_id,
            caption=caption,
            reply_markup=kb_mockup_actions(m),
        )
    else:
        await bot.send_message(
            callback.message.chat.id, caption, reply_markup=kb_mockup_actions(m)
        )
    await callback.answer()


# ---------- Удаление ----------

@router.callback_query(AdminCb.filter(F.action == "del_cat"))
async def cb_del_cat(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    cat = await crud.get_category(session, callback_data.id)
    if cat is None or not callback.message:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    await crud.delete_category(session, cat)
    await callback.answer("Категория удалена")
    cats = await crud.list_categories(session, only_active=False)
    kb = kb_categories_admin(cats) if cats else kb_back_admin()
    try:
        await callback.message.edit_text(
            "✅ Категория удалена.\n\n📂 Все категории:", reply_markup=kb
        )
    except Exception:
        await callback.message.answer(
            "✅ Категория удалена.\n\n📂 Все категории:", reply_markup=kb
        )


@router.callback_query(AdminCb.filter(F.action == "del_sub"))
async def cb_del_sub(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    sub = await crud.get_subcategory(session, callback_data.id)
    if sub is None or not callback.message:
        await callback.answer("Подкатегория не найдена", show_alert=True)
        return
    cat_id = sub.category_id
    await crud.delete_subcategory(session, sub)
    await callback.answer("Удалено")
    subs = await crud.list_subcategories(session, cat_id, only_active=False)
    kb = kb_subs_admin(subs, cat_id) if subs else kb_back_admin()
    try:
        await callback.message.edit_text(
            "✅ Подкатегория удалена.", reply_markup=kb
        )
    except Exception:
        await callback.message.answer("✅ Подкатегория удалена.", reply_markup=kb)


@router.callback_query(AdminCb.filter(F.action == "del_mockup"))
async def cb_del_mockup(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, bot: Bot
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    m = await crud.get_mockup(session, callback_data.id)
    if m is None or not callback.message:
        await callback.answer("Макет не найден", show_alert=True)
        return
    sub_id = m.subcategory_id
    await crud.delete_mockup(session, m)
    await callback.answer("Макет удалён")
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        callback.message.chat.id,
        "✅ Макет удалён.",
        reply_markup=kb_back_admin(),
    )


# ---------- Добавление КАТЕГОРИИ ----------

@router.callback_query(AdminCb.filter(F.action == "add_cat"))
async def cb_add_cat_start(
    callback: CallbackQuery, state: FSMContext
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    await state.set_state(AddCategory.name)
    if callback.message:
        await callback.message.answer(
            "Введи <b>название категории</b> (например, «Рестораны»):",
            reply_markup=kb_cancel(),
        )
    await callback.answer()


@router.message(AddCategory.name)
async def msg_add_cat_name(message: Message, state: FSMContext) -> None:
    if not message.from_user or not settings.is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуй ещё раз.")
        return
    await state.update_data(name=name)
    await state.set_state(AddCategory.emoji)
    await message.answer(
        "Отправь <b>эмодзи</b> для категории (одним символом, например 🍽).\n"
        "Или нажми «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(AddCategory.emoji, AdminCb.filter(F.action == "skip"))
async def cb_skip_cat_emoji(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(emoji=None)
    await state.set_state(AddCategory.description)
    if callback.message:
        await callback.message.answer(
            "Описание категории (необязательно). Можно «Пропустить».",
            reply_markup=kb_skip_or_cancel(),
        )
    await callback.answer()


@router.message(AddCategory.emoji)
async def msg_add_cat_emoji(message: Message, state: FSMContext) -> None:
    emoji = (message.text or "").strip()[:4]
    await state.update_data(emoji=emoji or None)
    await state.set_state(AddCategory.description)
    await message.answer(
        "Описание категории (необязательно). Можно «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(AddCategory.description, AdminCb.filter(F.action == "skip"))
async def cb_skip_cat_desc(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_add_category(callback, state, session, description=None)


@router.message(AddCategory.description)
async def msg_add_cat_desc(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_add_category(message, state, session, description=message.text)


async def _finalize_add_category(
    target: Message | CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    description: Optional[str],
) -> None:
    data = await state.get_data()
    cat = await crud.create_category(
        session,
        name=data["name"],
        emoji=data.get("emoji"),
        description=description,
    )
    await state.clear()
    text = f"✅ Категория добавлена: <b>{cat.display}</b> (ID {cat.id})"
    if isinstance(target, CallbackQuery):
        if target.message:
            await target.message.answer(text, reply_markup=kb_admin_menu())
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb_admin_menu())


# ---------- Добавление ПОДКАТЕГОРИИ ----------

@router.callback_query(AdminCb.filter(F.action == "add_sub"))
async def cb_add_sub_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    cats = await crud.list_categories(session, only_active=False)
    if not cats:
        await callback.answer("Сначала создай категорию", show_alert=True)
        return
    await state.set_state(AddSubcategory.category_id)
    if callback.message:
        await callback.message.answer(
            "Выбери категорию, в которую добавляем подкатегорию:",
            reply_markup=kb_pick_category(cats, action="pick_cat_for_sub"),
        )
    await callback.answer()


@router.callback_query(
    AddSubcategory.category_id, AdminCb.filter(F.action == "pick_cat_for_sub")
)
async def cb_picked_cat_for_sub(
    callback: CallbackQuery, callback_data: AdminCb, state: FSMContext
) -> None:
    await state.update_data(category_id=callback_data.id)
    await state.set_state(AddSubcategory.name)
    if callback.message:
        await callback.message.answer(
            "Введи название подкатегории (например, «Грузинская кухня»):",
            reply_markup=kb_cancel(),
        )
    await callback.answer()


@router.message(AddSubcategory.name)
async def msg_add_sub_name(message: Message, state: FSMContext) -> None:
    if not message.from_user or not settings.is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(name=name)
    await state.set_state(AddSubcategory.description)
    await message.answer(
        "Описание подкатегории (необязательно). Можно «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(
    AddSubcategory.description, AdminCb.filter(F.action == "skip")
)
async def cb_skip_sub_desc(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_add_sub(callback, state, session, description=None)


@router.message(AddSubcategory.description)
async def msg_add_sub_desc(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_add_sub(message, state, session, description=message.text)


async def _finalize_add_sub(
    target: Message | CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    description: Optional[str],
) -> None:
    data = await state.get_data()
    sub = await crud.create_subcategory(
        session,
        category_id=data["category_id"],
        name=data["name"],
        description=description,
    )
    await state.clear()
    text = f"✅ Подкатегория добавлена: <b>{sub.name}</b> (ID {sub.id})"
    if isinstance(target, CallbackQuery):
        if target.message:
            await target.message.answer(text, reply_markup=kb_admin_menu())
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb_admin_menu())


# ---------- Добавление МАКЕТА ----------

@router.callback_query(AdminCb.filter(F.action == "add_mockup"))
async def cb_add_mockup_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    cats = await crud.list_categories(session, only_active=False)
    if not cats:
        await callback.answer("Сначала создай категорию", show_alert=True)
        return
    await state.set_state(AddMockup.subcategory_id)
    await state.update_data(_pick_step="cat")
    if callback.message:
        await callback.message.answer(
            "Шаг 1/2 — выбери категорию:",
            reply_markup=kb_pick_category(cats, action="pick_cat_for_mockup"),
        )
    await callback.answer()


@router.callback_query(
    AddMockup.subcategory_id, AdminCb.filter(F.action == "pick_cat_for_mockup")
)
async def cb_pick_cat_for_mockup(
    callback: CallbackQuery,
    callback_data: AdminCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    subs = await crud.list_subcategories(session, callback_data.id, only_active=False)
    if not subs:
        await callback.answer(
            "В этой категории нет подкатегорий. Сначала добавь подкатегорию.",
            show_alert=True,
        )
        return
    if callback.message:
        await callback.message.answer(
            "Шаг 2/2 — выбери подкатегорию:",
            reply_markup=kb_pick_subcategory(subs, action="pick_sub_for_mockup"),
        )
    await callback.answer()


@router.callback_query(
    AddMockup.subcategory_id, AdminCb.filter(F.action == "pick_sub_for_mockup")
)
async def cb_pick_sub_for_mockup(
    callback: CallbackQuery, callback_data: AdminCb, state: FSMContext
) -> None:
    await state.update_data(subcategory_id=callback_data.id)
    await state.set_state(AddMockup.title)
    if callback.message:
        await callback.message.answer(
            "Введи <b>название макета</b> (например, «Сайт грузинского ресторана №1»):",
            reply_markup=kb_cancel(),
        )
    await callback.answer()


@router.message(AddMockup.title)
async def msg_mockup_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(title=title)
    await state.set_state(AddMockup.description)
    await message.answer(
        "Описание макета (необязательно). Можно «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(AddMockup.description, AdminCb.filter(F.action == "skip"))
async def cb_skip_mockup_desc(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(AddMockup.photo)
    if callback.message:
        await callback.message.answer(
            "Пришли <b>скриншот макета</b> (фото). Или «Пропустить» — добавим без картинки.",
            reply_markup=kb_skip_or_cancel(),
        )
    await callback.answer()


@router.message(AddMockup.description)
async def msg_mockup_desc(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(AddMockup.photo)
    await message.answer(
        "Пришли <b>скриншот макета</b> (фото). Или «Пропустить» — добавим без картинки.",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(AddMockup.photo, AdminCb.filter(F.action == "skip"))
async def cb_skip_mockup_photo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(photo_file_id=None)
    await state.set_state(AddMockup.figma)
    if callback.message:
        await callback.message.answer(
            "Ссылка на Figma (необязательно). Если её нет — нажми «Пропустить».",
            reply_markup=kb_skip_or_cancel(),
        )
    await callback.answer()


@router.message(AddMockup.photo, F.photo)
async def msg_mockup_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        return
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await state.set_state(AddMockup.figma)
    await message.answer(
        "Скриншот сохранён ✅\n"
        "Ссылка на Figma (необязательно). Если её нет — нажми «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.message(AddMockup.photo)
async def msg_mockup_photo_invalid(message: Message) -> None:
    await message.answer(
        "Жду именно фото 📸 (не файлом). Или нажми «Пропустить»."
    )


@router.callback_query(AddMockup.figma, AdminCb.filter(F.action == "skip"))
async def cb_skip_mockup_figma(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(figma_link=None)
    await state.set_state(AddMockup.price)
    if callback.message:
        await callback.message.answer(
            "Цена в формате «<число> <валюта>», например «499 USD».\n"
            "Если хочется «по запросу» — нажми «Пропустить».",
            reply_markup=kb_skip_or_cancel(),
        )
    await callback.answer()


@router.message(AddMockup.figma)
async def msg_mockup_figma(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text and not text.startswith("http"):
        await message.answer("Ссылка должна начинаться с http(s)://. Попробуй снова или «Пропустить».")
        return
    await state.update_data(figma_link=text or None)
    await state.set_state(AddMockup.price)
    await message.answer(
        "Цена в формате «<число> <валюта>», например «499 USD».\n"
        "Если хочется «по запросу» — «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(AddMockup.price, AdminCb.filter(F.action == "skip"))
async def cb_skip_mockup_price(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(price_cents=None, currency=None)
    await state.set_state(AddMockup.features)
    if callback.message:
        await callback.message.answer(
            "Список фич (по строке на пункт). Например:\n"
            "<code>Адаптивный дизайн\nКорзина и оплата\nЛичный кабинет</code>\n\n"
            "Или «Пропустить».",
            reply_markup=kb_skip_or_cancel(),
        )
    await callback.answer()


@router.message(AddMockup.price)
async def msg_mockup_price(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    parts = text.split()
    try:
        if len(parts) == 1:
            amount = float(parts[0])
            currency = settings.default_currency
        elif len(parts) >= 2:
            amount = float(parts[0])
            currency = parts[1].upper()
        else:
            raise ValueError
        price_cents = int(round(amount * 100))
    except (ValueError, IndexError):
        await message.answer(
            "Не разобрал цену. Пример: <code>499 USD</code>. Или «Пропустить»."
        )
        return
    await state.update_data(price_cents=price_cents, currency=currency)
    await state.set_state(AddMockup.features)
    await message.answer(
        "Список фич (по строке на пункт) или «Пропустить».",
        reply_markup=kb_skip_or_cancel(),
    )


@router.callback_query(AddMockup.features, AdminCb.filter(F.action == "skip"))
async def cb_skip_mockup_features(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_add_mockup(callback, state, session, features=None)


@router.message(AddMockup.features)
async def msg_mockup_features(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_add_mockup(message, state, session, features=message.text)


async def _finalize_add_mockup(
    target: Message | CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    features: Optional[str],
) -> None:
    data = await state.get_data()
    mockup = await crud.create_mockup(
        session,
        subcategory_id=data["subcategory_id"],
        title=data["title"],
        description=data.get("description"),
        photo_file_id=data.get("photo_file_id"),
        figma_link=data.get("figma_link"),
        price_cents=data.get("price_cents"),
        currency=data.get("currency"),
        features=features,
    )
    await state.clear()
    text = f"✅ Макет добавлен: <b>{mockup.title}</b> (ID {mockup.id})"
    if isinstance(target, CallbackQuery):
        if target.message:
            await target.message.answer(text, reply_markup=kb_admin_menu())
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb_admin_menu())


# ---------- Заявки ----------

@router.callback_query(AdminCb.filter(F.action == "leads"))
async def cb_leads(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    reqs = await crud.list_contact_requests(session, only_new=False, limit=20)
    if not reqs:
        text = "Заявок пока нет."
        kb = kb_back_admin()
    else:
        lines = ["📨 <b>Последние заявки:</b>\n"]
        for r in reqs:
            user = r.user
            name = user.display_name if user else "—"
            mark = "🟢" if r.status == "new" else "⚪️"
            mtitle = f" • {r.mockup.title}" if r.mockup else ""
            preview = (r.message or "—")[:80]
            lines.append(
                f"{mark} #{r.id} — {name}{mtitle}\n   <i>{preview}</i>"
            )
        text = "\n".join(lines)
        kb = kb_back_admin()
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "lead_done"))
async def cb_lead_done(
    callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession
) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    await crud.mark_contact_request_done(session, callback_data.id)
    await callback.answer("Заявка закрыта ✅")


# ---------- Статистика ----------

@router.callback_query(AdminCb.filter(F.action == "stats"))
async def cb_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True)
        return
    users = await crud.count_users(session)
    mockups = await crud.count_mockups(session)
    leads = await crud.list_contact_requests(session, only_new=True, limit=1000)
    cats = await crud.list_categories(session, only_active=False)
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👤 Пользователей: <b>{users}</b>\n"
        f"📂 Категорий: <b>{len(cats)}</b>\n"
        f"🖼 Макетов: <b>{mockups}</b>\n"
        f"📨 Открытых заявок: <b>{len(leads)}</b>"
    )
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb_back_admin())
        except Exception:
            await callback.message.answer(text, reply_markup=kb_back_admin())
    await callback.answer()
