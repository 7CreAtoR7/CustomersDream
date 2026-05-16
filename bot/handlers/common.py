from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.keyboards.callbacks import AgreeCb, NavCb
from bot.keyboards.user_kb import (
    kb_agreement,
    kb_agreement_full,
    kb_back_to_menu,
    kb_main_menu,
    kb_webapp,
)
from bot.services import crud
from bot.utils import texts

router = Router(name="common")


async def _show_main_menu(target: Message | CallbackQuery) -> None:
    if isinstance(target, CallbackQuery):
        if target.message:
            try:
                await target.message.edit_text(texts.MAIN_MENU, reply_markup=kb_main_menu())
            except Exception:
                await target.message.answer(texts.MAIN_MENU, reply_markup=kb_main_menu())
        await target.answer()
    else:
        await target.answer(texts.MAIN_MENU, reply_markup=kb_main_menu())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    if not message.from_user:
        return

    user = await crud.get_or_create_user(
        session,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code,
        is_admin=settings.is_admin(message.from_user.id),
    )

    if not user.agreed_to_terms:
        await message.answer(texts.WELCOME)
        await message.answer(texts.AGREEMENT_INTRO, reply_markup=kb_agreement())
        return

    await message.answer(texts.WELCOME, reply_markup=kb_webapp())


@router.callback_query(NavCb.filter(F.to == "agreement"))
async def cb_show_agreement(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        return
    user = await session.get(User, callback.from_user.id)
    kb = kb_back_to_menu() if (user and user.agreed_to_terms) else kb_agreement_full()
    try:
        await callback.message.edit_text(texts.AGREEMENT_TEXT, reply_markup=kb)
    except Exception:
        await callback.message.answer(texts.AGREEMENT_TEXT, reply_markup=kb)
    await callback.answer()


@router.callback_query(AgreeCb.filter())
async def cb_agree(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not callback.message:
        return
    user = await crud.get_or_create_user(
        session,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        language_code=callback.from_user.language_code,
        is_admin=settings.is_admin(callback.from_user.id),
    )
    if not user.agreed_to_terms:
        await crud.set_user_agreed(session, user)
    await callback.answer("Спасибо! Соглашение принято ✅", show_alert=False)
    try:
        await callback.message.edit_text(texts.MAIN_MENU, reply_markup=kb_main_menu())
    except Exception:
        await callback.message.answer(texts.MAIN_MENU, reply_markup=kb_main_menu())


@router.callback_query(NavCb.filter(F.to == "menu"))
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _show_main_menu(callback)


@router.callback_query(NavCb.filter(F.to == "help"))
async def cb_help(callback: CallbackQuery) -> None:
    if not callback.message:
        return
    text = (
        "❓ <b>Как пользоваться ботом</b>\n\n"
        "1. Жми «🎨 Каталог макетов» и выбирай категорию бизнеса.\n"
        "2. Внутри категории выбирай подкатегорию (например, «Грузинская кухня»).\n"
        "3. Листай макеты, нажимай ❤️, чтобы сохранить понравившиеся.\n"
        "4. Когда определишься — жми «💬 Хочу этот сайт» под макетом или «Связаться "
        "с менеджером» в главном меню.\n\n"
        "Команды:\n"
        "/start — главное меню\n"
        "/menu — главное меню\n"
        "/likes — мои избранные макеты"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb_back_to_menu())
    except Exception:
        await callback.message.answer(text, reply_markup=kb_back_to_menu())
    await callback.answer()
