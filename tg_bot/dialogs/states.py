from aiogram.filters.state import StatesGroup, State


class MainDialogStates(StatesGroup):
    greeting = State()
    explanation = State()
    photo_upload = State()  # Загрузка фото пользователя
    photo_not_uploaded = State()
    description = State()  # Ввод описания для фотографии
    description_not_provided = State()
    generating = State()
    generated_success = State()
    generated_failure = State()

