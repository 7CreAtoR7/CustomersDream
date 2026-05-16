"""Типобезопасные callback_data на базе aiogram CallbackData."""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class CategoryCb(CallbackData, prefix="cat"):
    id: int


class SubcategoryCb(CallbackData, prefix="sub"):
    id: int


class MockupCb(CallbackData, prefix="mk"):
    id: int
    # 'view' | 'like' | 'contact' | 'next' | 'prev'
    action: str = "view"


class NavCb(CallbackData, prefix="nav"):
    # 'menu' | 'browse' | 'likes' | 'contact' | 'agreement' | 'help' | 'back_to_cats' |
    # 'back_to_subs' (при этом id = category_id)
    to: str
    id: int = 0


class AgreeCb(CallbackData, prefix="agree"):
    pass


# ---------- Админка ----------

class AdminCb(CallbackData, prefix="adm"):
    # 'menu' | 'cats' | 'add_cat' | 'add_sub' | 'add_mockup' |
    # 'leads' | 'stats' | 'users' | 'cancel' |
    # 'pick_cat_for_sub' | 'pick_sub_for_mockup' |
    # 'edit_cat' | 'del_cat' | 'edit_sub' | 'del_sub' | 'edit_mockup' | 'del_mockup' |
    # 'lead_done'
    action: str
    id: int = 0
