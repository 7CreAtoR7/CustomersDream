from __future__ import annotations

from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Mockup, User
from bot.keyboards.callbacks import (
    CategoryCb,
    MockupCb,
    NavCb,
    SubcategoryCb,
)
from bot.keyboards.user_kb import (
    kb_back_to_menu,
    kb_categories,
    kb_contact_manager,
    kb_main_menu,
    kb_mockup_view,
    kb_subcategories,
)
from bot.services import crud
from bot.states.user_states import ContactFlow
from bot.utils import texts

router = Router(name="user")


# ---------- Гард: соглашение принято? ----------

async def _ensure_agreed(callback: CallbackQuery, session: AsyncSession) -> bool:
    if not callback.from_user:
        return False
    user = await session.get(User, callback.from_user.id)
    if user and user.agreed_to_terms:
        return True
    await callback.answer(texts.AGREEMENT_REQUIRED, show_alert=True)
    return False


# ---------- Каталог категорий ----------

@router.callback_query(NavCb.filter(F.to == "browse"))
async def cb_browse(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message:
        return
    cats = await crud.list_categories(session)
    if not cats:
        text = "Каталог пока пуст. Загляни позже 🙂"
        try:
            await callback.message.edit_text(text, reply_markup=kb_back_to_menu())
        except Exception:
            await callback.message.answer(text, reply_markup=kb_back_to_menu())
    else:
        try:
            await callback.message.edit_text(
                texts.CHOOSE_CATEGORY, reply_markup=kb_categories(cats)
            )
        except Exception:
            await callback.message.answer(
                texts.CHOOSE_CATEGORY, reply_markup=kb_categories(cats)
            )
    await callback.answer()


@router.callback_query(CategoryCb.filter())
async def cb_open_category(
    callback: CallbackQuery, callback_data: CategoryCb, session: AsyncSession
) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message:
        return
    cat = await crud.get_category(session, callback_data.id)
    if cat is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    subs = await crud.list_subcategories(session, cat.id)
    text = texts.CHOOSE_SUBCATEGORY.format(category=cat.display)
    if not subs:
        text += "\n\nПока пусто, но скоро появятся макеты 🙂"
        kb = kb_back_to_menu()
    else:
        kb = kb_subcategories(subs, cat.id)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(NavCb.filter(F.to == "back_to_subs"))
async def cb_back_to_subs(
    callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, bot: Bot
) -> None:
    """После просмотра конкретного макета (фото) возвращаемся к списку подкатегорий."""
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message:
        return
    cat = await crud.get_category(session, callback_data.id)
    if cat is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    subs = await crud.list_subcategories(session, cat.id)
    text = texts.CHOOSE_SUBCATEGORY.format(category=cat.display)
    kb = kb_subcategories(subs, cat.id) if subs else kb_back_to_menu()
    if not subs:
        text += "\n\nПока пусто 🙂"
    # Текущее сообщение, скорее всего, фото — отправляем новое
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        chat_id=callback.message.chat.id, text=text, reply_markup=kb
    )
    await callback.answer()


# ---------- Подкатегория -> первый макет ----------

@router.callback_query(SubcategoryCb.filter())
async def cb_open_subcategory(
    callback: CallbackQuery,
    callback_data: SubcategoryCb,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message:
        return
    sub = await crud.get_subcategory(session, callback_data.id)
    if sub is None:
        await callback.answer("Подкатегория не найдена", show_alert=True)
        return
    mockups = await crud.list_mockups(session, sub.id)
    if not mockups:
        try:
            await callback.message.edit_text(
                texts.NO_MOCKUPS, reply_markup=kb_back_to_menu()
            )
        except Exception:
            await callback.message.answer(
                texts.NO_MOCKUPS, reply_markup=kb_back_to_menu()
            )
        await callback.answer()
        return

    await _send_mockup(
        bot=bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id if callback.from_user else 0,
        mockup=mockups[0],
        session=session,
        replace_message=callback.message,
    )
    await callback.answer()


# ---------- Просмотр макета ----------

def _format_mockup_caption(mockup: Mockup) -> str:
    lines = [f"<b>{mockup.title}</b>"]
    sub = mockup.subcategory
    cat = sub.category if sub else None
    if sub and cat:
        lines.append(f"<i>{cat.display} → {sub.name}</i>")
    if mockup.description:
        lines.append("")
        lines.append(mockup.description)
    if mockup.features:
        lines.append("")
        lines.append("<b>Что включено:</b>")
        for line in mockup.features.splitlines():
            line = line.strip(" •-—")
            if line:
                lines.append(f"• {line}")
    if mockup.price_cents:
        currency = mockup.currency or settings.default_currency
        amount = mockup.price_cents / 100
        lines.append("")
        lines.append(f"<b>Стоимость:</b> {amount:.2f} {currency}")
    else:
        lines.append("")
        lines.append("<b>Стоимость:</b> по запросу")
    return "\n".join(lines)


async def _send_mockup(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    mockup: Mockup,
    session: AsyncSession,
    replace_message: Optional[Message] = None,
) -> None:
    siblings = await crud.list_mockups(session, mockup.subcategory_id)
    ids = [m.id for m in siblings]
    try:
        idx = ids.index(mockup.id)
    except ValueError:
        idx = 0
    has_prev = idx > 0
    has_next = idx < len(ids) - 1

    is_liked = await crud.is_liked(session, user_id, mockup.id)
    caption = _format_mockup_caption(mockup)
    sub = mockup.subcategory
    cat_id = sub.category_id if sub else 0
    kb = kb_mockup_view(
        mockup,
        is_liked=is_liked,
        has_prev=has_prev,
        has_next=has_next,
        category_id=cat_id,
    )

    if replace_message is not None:
        try:
            await replace_message.delete()
        except Exception:
            pass

    if mockup.photo_file_id:
        await bot.send_photo(
            chat_id=chat_id,
            photo=mockup.photo_file_id,
            caption=caption,
            reply_markup=kb,
        )
    else:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=kb)


@router.callback_query(MockupCb.filter(F.action == "like"))
async def cb_like(
    callback: CallbackQuery, callback_data: MockupCb, session: AsyncSession
) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message or not callback.from_user:
        return
    mockup = await crud.get_mockup(session, callback_data.id)
    if mockup is None:
        await callback.answer("Макет не найден", show_alert=True)
        return
    now_liked = await crud.toggle_like(session, callback.from_user.id, mockup.id)

    sub = mockup.subcategory
    cat_id = sub.category_id if sub else 0
    siblings = await crud.list_mockups(session, mockup.subcategory_id)
    ids = [m.id for m in siblings]
    idx = ids.index(mockup.id) if mockup.id in ids else 0
    has_prev = idx > 0
    has_next = idx < len(ids) - 1

    new_kb = kb_mockup_view(
        mockup,
        is_liked=now_liked,
        has_prev=has_prev,
        has_next=has_next,
        category_id=cat_id,
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except Exception:
        pass
    await callback.answer("Добавлено в избранное ❤️" if now_liked else "Убрано из избранного")


@router.callback_query(MockupCb.filter(F.action.in_({"prev", "next"})))
async def cb_navigate(
    callback: CallbackQuery,
    callback_data: MockupCb,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message or not callback.from_user:
        return
    current = await crud.get_mockup(session, callback_data.id)
    if current is None:
        await callback.answer("Макет не найден", show_alert=True)
        return
    siblings = await crud.list_mockups(session, current.subcategory_id)
    ids = [m.id for m in siblings]
    try:
        idx = ids.index(current.id)
    except ValueError:
        idx = 0
    if callback_data.action == "next":
        idx = min(idx + 1, len(siblings) - 1)
    else:
        idx = max(idx - 1, 0)
    target = siblings[idx]
    # Перезагружаем с join'ами
    target = await crud.get_mockup(session, target.id) or target
    await _send_mockup(
        bot=bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        mockup=target,
        session=session,
        replace_message=callback.message,
    )
    await callback.answer()


# ---------- Избранное ----------

@router.callback_query(NavCb.filter(F.to == "likes"))
async def cb_likes(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message or not callback.from_user:
        return
    likes = await crud.list_user_likes(session, callback.from_user.id)
    if not likes:
        try:
            await callback.message.edit_text(
                texts.NO_LIKES, reply_markup=kb_back_to_menu()
            )
        except Exception:
            await callback.message.answer(
                texts.NO_LIKES, reply_markup=kb_back_to_menu()
            )
        await callback.answer()
        return

    text_lines = ["❤️ <b>Твои избранные макеты:</b>", ""]
    for m in likes:
        sub = m.subcategory
        cat = sub.category if sub else None
        path = f"{cat.display} → {sub.name}" if (cat and sub) else ""
        text_lines.append(f"• <b>{m.title}</b> — {path}")
    text_lines.append("")
    text_lines.append("Чтобы открыть макет — найди его в каталоге.")
    text_lines.append("Хочешь воплотить — жми «💬 Связаться с менеджером».")
    try:
        await callback.message.edit_text(
            "\n".join(text_lines), reply_markup=kb_back_to_menu()
        )
    except Exception:
        await callback.message.answer(
            "\n".join(text_lines), reply_markup=kb_back_to_menu()
        )
    await callback.answer()


@router.message(Command("likes"))
async def cmd_likes(message: Message, session: AsyncSession) -> None:
    if not message.from_user:
        return
    likes = await crud.list_user_likes(session, message.from_user.id)
    if not likes:
        await message.answer(texts.NO_LIKES, reply_markup=kb_back_to_menu())
        return
    text_lines = ["❤️ <b>Твои избранные макеты:</b>", ""]
    for m in likes:
        sub = m.subcategory
        cat = sub.category if sub else None
        path = f"{cat.display} → {sub.name}" if (cat and sub) else ""
        text_lines.append(f"• <b>{m.title}</b> — {path}")
    await message.answer("\n".join(text_lines), reply_markup=kb_back_to_menu())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.MAIN_MENU, reply_markup=kb_main_menu())


# ---------- Связь с менеджером ----------

@router.callback_query(NavCb.filter(F.to == "contact"))
async def cb_contact(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message:
        return
    await state.set_state(ContactFlow.waiting_message)
    await state.update_data(mockup_id=None)
    try:
        await callback.message.edit_text(
            texts.CONTACT_PROMPT,
            reply_markup=kb_contact_manager(settings.manager_usernames),
        )
    except Exception:
        await callback.message.answer(
            texts.CONTACT_PROMPT,
            reply_markup=kb_contact_manager(settings.manager_usernames),
        )
    await callback.answer()


@router.callback_query(MockupCb.filter(F.action == "contact"))
async def cb_contact_about_mockup(
    callback: CallbackQuery,
    callback_data: MockupCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await _ensure_agreed(callback, session):
        return
    if not callback.message:
        return
    mockup = await crud.get_mockup(session, callback_data.id)
    if mockup is None:
        await callback.answer("Макет не найден", show_alert=True)
        return
    await state.set_state(ContactFlow.waiting_message)
    await state.update_data(mockup_id=mockup.id)
    text = (
        f"💬 <b>Заявка по макету:</b> {mockup.title}\n\n"
        "Напиши пожелания: бюджет, сроки, нужный функционал. Менеджер увидит "
        "ссылку на макет и свяжется с тобой."
    )
    await callback.message.answer(
        text, reply_markup=kb_contact_manager(settings.manager_usernames)
    )
    await callback.answer()


@router.message(ContactFlow.waiting_message)
async def msg_contact_text(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    if not message.from_user:
        return
    data = await state.get_data()
    mockup_id = data.get("mockup_id")
    text = message.text or message.caption or ""
    req = await crud.create_contact_request(
        session,
        user_id=message.from_user.id,
        mockup_id=mockup_id,
        message=text,
    )
    await state.clear()

    managers = settings.manager_usernames
    user_text = (
        texts.CONTACT_DONE.format(
            manager=", ".join(f"@{u}" for u in managers)
        )
        if managers
        else texts.CONTACT_NO_MANAGER
    )
    await message.answer(user_text, reply_markup=kb_main_menu())

    # Уведомляем админов
    user = await session.get(User, message.from_user.id)
    name = user.display_name if user else f"id{message.from_user.id}"
    mockup_part = ""
    if mockup_id:
        mockup = await crud.get_mockup(session, mockup_id)
        if mockup:
            sub = mockup.subcategory
            cat = sub.category if sub else None
            path = f"{cat.display} → {sub.name}" if (cat and sub) else ""
            mockup_part = f"\n📌 Макет: <b>{mockup.title}</b> ({path})"

    notify = (
        f"📨 <b>Новая заявка #{req.id}</b>\n"
        f"👤 {name}"
        f"{(' (@' + user.username + ')') if user and user.username else ''}"
        f"\n🆔 <code>{message.from_user.id}</code>"
        f"{mockup_part}\n\n"
        f"💬 <i>{text or '(без сообщения)'}</i>"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, notify)
        except Exception:
            pass
