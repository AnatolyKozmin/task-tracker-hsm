from aiogram.fsm.state import State, StatesGroup


class ProjectStates(StatesGroup):
    """Состояния для работы с проектами"""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_edit_name = State()
    waiting_for_edit_description = State()


class TaskStates(StatesGroup):
    """Состояния для работы с задачами"""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_assignees = State()
    waiting_for_edit_title = State()
    waiting_for_edit_description = State()
    waiting_for_edit_deadline = State()


class MemberStates(StatesGroup):
    """Состояния для работы с участниками"""
    waiting_for_username = State()
    waiting_for_role = State()


class ReminderStates(StatesGroup):
    """Состояния для настройки напоминаний"""
    waiting_for_custom_time = State()

