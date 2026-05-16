from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import (
    Category,
    ContactRequest,
    Like,
    Mockup,
    Subcategory,
    User,
)


# ---------------- Users ----------------

async def get_or_create_user(
    session: AsyncSession,
    *,
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    language_code: Optional[str],
    is_admin: bool = False,
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_admin=is_admin,
        )
        session.add(user)
        await session.flush()
    else:
        # Обновляем актуальные данные при каждом /start
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.language_code = language_code
        if is_admin and not user.is_admin:
            user.is_admin = True
    return user


async def set_user_agreed(session: AsyncSession, user: User) -> None:
    user.agreed_to_terms = True
    user.agreed_at = datetime.utcnow()


async def list_users(session: AsyncSession, limit: int = 50) -> Sequence[User]:
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return int(result.scalar_one())


# ---------------- Categories ----------------

async def list_categories(session: AsyncSession, only_active: bool = True) -> List[Category]:
    stmt = select(Category).order_by(Category.position, Category.id)
    if only_active:
        stmt = stmt.where(Category.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_category(session: AsyncSession, category_id: int) -> Optional[Category]:
    return await session.get(Category, category_id)


async def create_category(
    session: AsyncSession,
    *,
    name: str,
    emoji: Optional[str] = None,
    description: Optional[str] = None,
) -> Category:
    cat = Category(name=name, emoji=emoji, description=description)
    session.add(cat)
    await session.flush()
    return cat


async def update_category(
    session: AsyncSession,
    category: Category,
    *,
    name: Optional[str] = None,
    emoji: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Category:
    if name is not None:
        category.name = name
    if emoji is not None:
        category.emoji = emoji
    if description is not None:
        category.description = description
    if is_active is not None:
        category.is_active = is_active
    return category


async def delete_category(session: AsyncSession, category: Category) -> None:
    await session.delete(category)


# ---------------- Subcategories ----------------

async def list_subcategories(
    session: AsyncSession, category_id: int, only_active: bool = True
) -> List[Subcategory]:
    stmt = (
        select(Subcategory)
        .where(Subcategory.category_id == category_id)
        .order_by(Subcategory.position, Subcategory.id)
    )
    if only_active:
        stmt = stmt.where(Subcategory.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_subcategory(
    session: AsyncSession, sub_id: int
) -> Optional[Subcategory]:
    result = await session.execute(
        select(Subcategory)
        .where(Subcategory.id == sub_id)
        .options(selectinload(Subcategory.category))
    )
    return result.scalar_one_or_none()


async def create_subcategory(
    session: AsyncSession,
    *,
    category_id: int,
    name: str,
    description: Optional[str] = None,
) -> Subcategory:
    sub = Subcategory(category_id=category_id, name=name, description=description)
    session.add(sub)
    await session.flush()
    return sub


async def delete_subcategory(session: AsyncSession, sub: Subcategory) -> None:
    await session.delete(sub)


# ---------------- Mockups ----------------

async def list_mockups(
    session: AsyncSession, sub_id: int, only_active: bool = True
) -> List[Mockup]:
    stmt = (
        select(Mockup)
        .where(Mockup.subcategory_id == sub_id)
        .order_by(Mockup.position, Mockup.id)
    )
    if only_active:
        stmt = stmt.where(Mockup.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_mockup(session: AsyncSession, mockup_id: int) -> Optional[Mockup]:
    result = await session.execute(
        select(Mockup)
        .where(Mockup.id == mockup_id)
        .options(
            selectinload(Mockup.subcategory).selectinload(Subcategory.category)
        )
    )
    return result.scalar_one_or_none()


async def create_mockup(
    session: AsyncSession,
    *,
    subcategory_id: int,
    title: str,
    description: Optional[str] = None,
    photo_file_id: Optional[str] = None,
    figma_link: Optional[str] = None,
    price_cents: Optional[int] = None,
    currency: Optional[str] = None,
    features: Optional[str] = None,
) -> Mockup:
    mockup = Mockup(
        subcategory_id=subcategory_id,
        title=title,
        description=description,
        photo_file_id=photo_file_id,
        figma_link=figma_link,
        price_cents=price_cents,
        currency=currency,
        features=features,
    )
    session.add(mockup)
    await session.flush()
    return mockup


async def update_mockup(session: AsyncSession, mockup: Mockup, **fields) -> Mockup:
    for key, value in fields.items():
        if value is None:
            continue
        if hasattr(mockup, key):
            setattr(mockup, key, value)
    return mockup


async def delete_mockup(session: AsyncSession, mockup: Mockup) -> None:
    await session.delete(mockup)


async def count_mockups(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Mockup.id)))
    return int(result.scalar_one())


# ---------------- Likes ----------------

async def toggle_like(session: AsyncSession, user_id: int, mockup_id: int) -> bool:
    """Тогглит лайк. Возвращает True, если теперь лайкнуто, False — если убрано."""
    existing = await session.execute(
        select(Like).where(Like.user_id == user_id, Like.mockup_id == mockup_id)
    )
    like = existing.scalar_one_or_none()
    if like:
        await session.delete(like)
        return False
    session.add(Like(user_id=user_id, mockup_id=mockup_id))
    await session.flush()
    return True


async def is_liked(session: AsyncSession, user_id: int, mockup_id: int) -> bool:
    result = await session.execute(
        select(Like.id).where(Like.user_id == user_id, Like.mockup_id == mockup_id)
    )
    return result.scalar_one_or_none() is not None


async def list_user_likes(session: AsyncSession, user_id: int) -> List[Mockup]:
    result = await session.execute(
        select(Mockup)
        .join(Like, Like.mockup_id == Mockup.id)
        .where(Like.user_id == user_id, Mockup.is_active.is_(True))
        .order_by(Like.created_at.desc())
        .options(
            selectinload(Mockup.subcategory).selectinload(Subcategory.category)
        )
    )
    return list(result.scalars().all())


async def count_user_likes(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count(Like.id)).where(Like.user_id == user_id)
    )
    return int(result.scalar_one())


# ---------------- Contact requests ----------------

async def create_contact_request(
    session: AsyncSession,
    *,
    user_id: int,
    mockup_id: Optional[int] = None,
    message: Optional[str] = None,
) -> ContactRequest:
    req = ContactRequest(user_id=user_id, mockup_id=mockup_id, message=message)
    session.add(req)
    await session.flush()
    return req


async def list_contact_requests(
    session: AsyncSession, only_new: bool = True, limit: int = 30
) -> List[ContactRequest]:
    stmt = (
        select(ContactRequest)
        .order_by(ContactRequest.created_at.desc())
        .limit(limit)
        .options(
            selectinload(ContactRequest.user),
            selectinload(ContactRequest.mockup),
        )
    )
    if only_new:
        stmt = stmt.where(ContactRequest.status == "new")
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_contact_request_done(
    session: AsyncSession, request_id: int
) -> Optional[ContactRequest]:
    req = await session.get(ContactRequest, request_id)
    if req is None:
        return None
    req.status = "closed"
    return req
