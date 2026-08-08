from aiogram.fsm.state import State, StatesGroup


class PaymentState(StatesGroup):

    waiting_amount = State()

    waiting_description = State()