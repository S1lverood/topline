from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    start = State()

class StateFAQ(StatesGroup):
    faq = State()


class StateSupport(StatesGroup):
    support_menu = State()
    input_message = State()


class StateSubscription(StatesGroup):
    subscription_general = State()
    choosing_month = State()
    choosing_payment = State()
    input_email = State()

class StateAccount(StatesGroup):
    account_general = State()
    list_payments = State()


class StateAdmin(StatesGroup):
    admin_menu = State()
    milling_menu = State()
    milling_active = State()
    statistics_menu = State()
    user_control_input = State()
    user_control_menu = State()
    user_control_message = State()
    user_control_add_time = State()