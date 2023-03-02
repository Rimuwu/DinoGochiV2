from telebot.asyncio_handler_backends import State, StatesGroup

class DinoStates(StatesGroup):
    choose_dino = State()

class SettingsStates(StatesGroup):
    settings_choose = State()
    rename_dino_step_name = State()
    rename_dino_step_confirmation = State()