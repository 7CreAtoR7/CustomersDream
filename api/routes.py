"""API routes for the Mini App frontend."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.db import async_session_factory
from bot.database.models import (
    Category,
    ContactRequest,
    Like,
    Mockup,
    Subcategory,
    User,
)

router = APIRouter()


async def get_session():
    async with async_session_factory() as session:
        yield session


# ---------- Pydantic schemas ----------

class CategoryOut(BaseModel):
    id: int
    name: str
    emoji: str | None
    description: str | None

class SubcategoryOut(BaseModel):
    id: int
    name: str
    description: str | None
    mockup_count: int = 0

class MockupOut(BaseModel):
    id: int
    title: str
    description: str | None
    photo_file_id: str | None
    photo_url: str | None
    figma_link: str | None
    price_cents: int | None
    currency: str | None
    features: str | None
    platform: str | None = None
    complexity: str | None = None
    is_liked: bool = False
    category_name: str | None = None
    subcategory_name: str | None = None


def _mockup_to_out(m: "Mockup", liked: bool = False) -> "MockupOut":
    photo_url = m.image_url or (f"/api/photo/{m.photo_file_id}" if m.photo_file_id else None)
    sub = m.subcategory
    cat = sub.category if sub else None
    return MockupOut(
        id=m.id,
        title=m.title,
        description=m.description,
        photo_file_id=m.photo_file_id,
        photo_url=photo_url,
        figma_link=m.figma_link,
        price_cents=m.price_cents,
        currency=m.currency,
        features=m.features,
        platform=m.platform,
        complexity=m.complexity,
        is_liked=liked,
        category_name=cat.name if cat else None,
        subcategory_name=sub.name if sub else None,
    )

class LikeResponse(BaseModel):
    liked: bool

class ContactIn(BaseModel):
    mockup_id: int | None = None
    message: str = ""
    request_type: str = "general"

class ContactOut(BaseModel):
    id: int
    status: str


# ---------- Endpoints ----------

@router.get("/categories", response_model=list[CategoryOut])
async def get_categories(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.position, Category.id)
    )
    return result.scalars().all()


@router.get("/categories/{category_id}/subcategories", response_model=list[SubcategoryOut])
async def get_subcategories(
    category_id: int,
    session: AsyncSession = Depends(get_session),
):
    cat = await session.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")

    result = await session.execute(
        select(Subcategory)
        .where(Subcategory.category_id == category_id, Subcategory.is_active.is_(True))
        .order_by(Subcategory.position, Subcategory.id)
    )
    subs = result.scalars().all()

    out = []
    for sub in subs:
        count_result = await session.execute(
            select(func.count(Mockup.id)).where(
                Mockup.subcategory_id == sub.id, Mockup.is_active.is_(True)
            )
        )
        count = count_result.scalar_one()
        out.append(SubcategoryOut(
            id=sub.id,
            name=sub.name,
            description=sub.description,
            mockup_count=count,
        ))
    return out


@router.get("/subcategories/{sub_id}/mockups", response_model=list[MockupOut])
async def get_mockups(
    sub_id: int,
    user_id: int = Query(0),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Mockup)
        .where(Mockup.subcategory_id == sub_id, Mockup.is_active.is_(True))
        .order_by(Mockup.position, Mockup.id)
        .options(selectinload(Mockup.subcategory).selectinload(Subcategory.category))
    )
    mockups = result.scalars().all()

    liked_ids = set()
    if user_id:
        like_rows = await session.execute(
            select(Like.mockup_id).where(Like.user_id == user_id)
        )
        liked_ids = set(like_rows.scalars().all())

    return [_mockup_to_out(m, m.id in liked_ids) for m in mockups]


@router.get("/mockups/all", response_model=list[MockupOut])
async def get_all_mockups(
    user_id: int = Query(0),
    platform: Optional[str] = Query(None),
    complexity: Optional[str] = Query(None),
    price_min: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Flat list of all mockups with optional filters (for filter chips)."""
    query = (
        select(Mockup)
        .where(Mockup.is_active.is_(True))
        .order_by(Mockup.position, Mockup.id)
        .options(selectinload(Mockup.subcategory).selectinload(Subcategory.category))
    )
    if platform:
        query = query.where(Mockup.platform == platform)
    if complexity:
        query = query.where(Mockup.complexity == complexity)
    if price_min is not None:
        query = query.where(Mockup.price_cents >= price_min)
    if price_max is not None:
        query = query.where(Mockup.price_cents <= price_max)

    result = await session.execute(query)
    mockups = result.scalars().all()

    liked_ids = set()
    if user_id:
        like_rows = await session.execute(
            select(Like.mockup_id).where(Like.user_id == user_id)
        )
        liked_ids = set(like_rows.scalars().all())

    return [_mockup_to_out(m, m.id in liked_ids) for m in mockups]


@router.get("/mockups/{mockup_id}", response_model=MockupOut)
async def get_mockup(
    mockup_id: int,
    user_id: int = Query(0),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Mockup)
        .where(Mockup.id == mockup_id)
        .options(selectinload(Mockup.subcategory).selectinload(Subcategory.category))
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Mockup not found")

    liked = False
    if user_id:
        like_result = await session.execute(
            select(Like.id).where(Like.user_id == user_id, Like.mockup_id == m.id)
        )
        liked = like_result.scalar_one_or_none() is not None

    return _mockup_to_out(m, liked)


@router.post("/like/{mockup_id}", response_model=LikeResponse)
async def toggle_like(
    mockup_id: int,
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(Like).where(Like.user_id == user_id, Like.mockup_id == mockup_id)
    )
    like = existing.scalar_one_or_none()
    if like:
        await session.delete(like)
        await session.commit()
        return LikeResponse(liked=False)

    # Ensure the user row exists to satisfy the FK constraint (the Mini App may
    # call /like before /user/init has completed).
    user = await session.get(User, user_id)
    if user is None:
        session.add(User(id=user_id, agreed_to_terms=True))
        await session.flush()

    session.add(Like(user_id=user_id, mockup_id=mockup_id))
    await session.commit()
    return LikeResponse(liked=True)


@router.get("/favorites", response_model=list[MockupOut])
async def get_favorites(
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Mockup)
        .join(Like, Like.mockup_id == Mockup.id)
        .where(Like.user_id == user_id, Mockup.is_active.is_(True))
        .order_by(Like.created_at.desc())
        .options(selectinload(Mockup.subcategory).selectinload(Subcategory.category))
    )
    mockups = result.scalars().all()
    return [_mockup_to_out(m, True) for m in mockups]


@router.post("/contact", response_model=ContactOut)
async def create_contact(
    body: ContactIn,
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    # Make sure the user exists to satisfy the FK constraint (e.g. if /user/init
    # never completed or the Mini App is opened without Telegram init data).
    user = await session.get(User, user_id)
    if user is None:
        user = User(id=user_id, agreed_to_terms=True)
        session.add(user)
        await session.flush()

    req = ContactRequest(
        user_id=user_id,
        mockup_id=body.mockup_id,
        message=body.message,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)

    # Send Telegram notification to admin
    await _notify_admin(session, req, user_id, body.request_type)

    return ContactOut(id=req.id, status=req.status)


async def _notify_admin(session: AsyncSession, req: ContactRequest, user_id: int, request_type: str):
    """Send notification about new request to admin via Telegram Bot API."""
    import aiohttp
    from bot.config import settings

    if not settings.admin_ids or not settings.bot_token:
        return

    user = await session.get(User, user_id)
    name = "Unknown"
    username_str = ""
    if user:
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"id{user.id}"
        username_str = f" (@{user.username})" if user.username else ""

    icon = "📝" if request_type == "custom" else "💬"
    text = (
        f"{icon} <b>Новая заявка #{req.id}</b>\n"
        f"👤 {name}{username_str}\n"
        f"🆔 <code>{user_id}</code>\n\n"
        f"{req.message or '(без сообщения)'}"
    )

    try:
        async with aiohttp.ClientSession() as http:
            for admin_id in settings.admin_ids:
                url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
                await http.post(url, json={
                    "chat_id": admin_id,
                    "text": text,
                    "parse_mode": "HTML",
                })
    except Exception:
        pass


@router.get("/config")
async def get_public_config():
    """Return non-sensitive config for the Mini App frontend."""
    from bot.config import settings
    managers = settings.manager_usernames
    return {
        "crypto_usdt_trc20": settings.crypto_usdt_trc20 or "",
        "manager_username": managers[0] if managers else "",
        "manager_usernames": managers,
    }


@router.post("/user/init")
async def init_user(
    user_id: int = Query(...),
    username: str = Query(""),
    first_name: str = Query(""),
    last_name: str = Query(""),
    session: AsyncSession = Depends(get_session),
):
    """Called on Mini App open to register/update user."""
    user = await session.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            username=username or None,
            first_name=first_name or None,
            last_name=last_name or None,
            agreed_to_terms=True,
        )
        session.add(user)
    else:
        user.username = username or user.username
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
    await session.commit()
    return {"ok": True, "user_id": user_id}
