from aiogram.fsm.state import State, StatesGroup


class AddCategory(StatesGroup):
    name = State()
    emoji = State()
    description = State()


class AddSubcategory(StatesGroup):
    category_id = State()
    name = State()
    description = State()


class AddMockup(StatesGroup):
    subcategory_id = State()
    title = State()
    description = State()
    photo = State()
    figma = State()
    price = State()
    features = State()
