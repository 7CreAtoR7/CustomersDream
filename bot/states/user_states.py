from aiogram.fsm.state import State, StatesGroup


class ContactFlow(StatesGroup):
    waiting_message = State()
