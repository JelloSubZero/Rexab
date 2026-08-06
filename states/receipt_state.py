from aiogram.fsm.state import State, StatesGroup


class ReceiptState(StatesGroup):
    waiting_receipt = State()
    waiting_total = State()