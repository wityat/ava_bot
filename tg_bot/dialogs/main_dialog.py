import asyncio
import base64
import logging
from typing import Any, Dict, io

from aiogram import Bot, types
from aiogram.enums import ContentType

from aiogram_dialog import Dialog, DialogManager, Window, ChatEvent
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.manager.bg_manager import BgManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Select, SwitchTo, Button, Group, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Progress
import random

from tg_bot.database import GenerationJob, FaceImage
from tg_bot.dialogs.states import *
from tg_bot import kandinsky, face_swapper
from tg_bot.database.models import User


async def get_data_from_user(dialog_manager: DialogManager, **kwargs):
    user_data = dialog_manager.current_context().dialog_data
    return {
        "face_image": user_data.get("face_image"),
    }


async def get_progress(dialog_manager: DialogManager, **kwargs):
    return {
        "progress": dialog_manager.dialog_data.get("progress", 0),
        "remaining_seconds": dialog_manager.dialog_data.get("remaining_seconds", 90),
    }


async def get_final_image(dialog_manager: DialogManager, **kwargs):
    return {
        "final_image": MediaAttachment(ContentType.PHOTO, url=dialog_manager.dialog_data.get("final_image_url", ''))
    }


async def get_error(dialog_manager: DialogManager, **kwargs):
    return {
        "error": dialog_manager.dialog_data.get("error", 90),
    }


async def user_accept_rules(c: ChatEvent, dialog, manager: DialogManager):
    db_session = manager.middleware_data["db_session"]
    user: User = await User.get(db_session, c.from_user.id)
    user.accepted_terms = True
    await user.save(db_session)
    await manager.switch_to(state=MainDialogStates.photo_upload)


async def upload_photo(message: types.Message, dialog, manager: DialogManager):
    answers = [
        "Выглядишь потрясно)",
        "Здорово выглядишь)",
        "Кажется, ты не выспался?(",
        "Братик, вид у тебя поношенный....",
    ]
    logging.info("Функция upload_photo была вызвана")
    if message.photo:
        await message.answer(random.choice(answers))
        manager.current_context().dialog_data["face_image"] = message.photo[-1].file_id
        db_session = manager.middleware_data["db_session"]
        user: User = await User.get(db_session, tg_id=message.from_user.id)
        face_image = FaceImage(file_id=message.photo[-1].file_id)
        generation_job = GenerationJob(user=user, face_image=face_image)
        await face_image.save(db_session)
        await generation_job.save(db_session)
        manager.current_context().dialog_data["generation_job_id"] = await generation_job.awaitable_attrs.id
        await manager.switch_to(state=MainDialogStates.description)
    else:
        await manager.switch_to(state=MainDialogStates.photo_not_uploaded)


async def process_description(message: types.Message, dialog, manager: DialogManager):
    if message.text:
        manager.current_context().dialog_data["text"] = message.text

        db_session = manager.middleware_data["db_session"]
        generation_job = await GenerationJob.get(db_session, manager.current_context().dialog_data["generation_job_id"])
        generation_job.text = manager.current_context().dialog_data["text"]
        await generation_job.save(db_session)

        await manager.switch_to(state=MainDialogStates.generating)
        asyncio.create_task(process_generating(manager.bg(), dialog_data=manager.current_context().dialog_data))
    else:
        await manager.switch_to(state=MainDialogStates.description_not_provided)


async def process_description__with_already_set_text(message: types.Message, dialog, manager: DialogManager):
    db_session = manager.middleware_data["db_session"]
    old_generation_job = await GenerationJob.get(db_session, manager.current_context().dialog_data["generation_job_id"])
    new_generation_job = GenerationJob(
        text=old_generation_job.text,
        user=await old_generation_job.awaitable_attrs.user,
        face_image=await old_generation_job.awaitable_attrs.face_image,
    )
    await new_generation_job.save(db_session)

    await manager.switch_to(state=MainDialogStates.generating)
    asyncio.create_task(process_generating(manager.bg(), dialog_data=manager.current_context().dialog_data))


async def process_generating(manager_bg: BgManager, dialog_data):
    bot: Bot = manager_bg.bot
    text = dialog_data["text"]
    progress_data = {
        "progress": 0,
        "remaining_seconds": 100
    }
    await manager_bg.update(progress_data)
    try:
        logging.warning("START")
        images = await kandinsky.generate(text, manager_bg, progress_data=progress_data)
        logging.warning("kandinsky DONE")
        generated_image = base64.b64decode(images[0])
        face_image = dialog_data.get("face_image")
        face_image_data: io.BytesIO = await bot.download(face_image)
        logging.warning("swapping face START")
        urls = await face_swapper.swap(generated_image,
                                       face_image_data.getvalue(),
                                       manager=manager_bg,
                                       progress_data=progress_data
                                       )
        logging.warning("swapping face DONE")
        await manager_bg.update({"final_image_url": urls[0]})
    except Exception as e:
        logging.error(str(e))
        await manager_bg.switch_to(MainDialogStates.generated_failure)
    else:
        await manager_bg.switch_to(MainDialogStates.generated_success)


ui = Dialog(
    Window(
        Const("""Привет! Я помогу тебе создать новую аватарку!
Но сначала нужно принять правила использования сервиса.
Жми кнопку 'Принять'."""),
        Button(Const("✅ Принять"), id="accept", on_click=user_accept_rules),
        Url(Const("🧾 Правила"), Const("https://example.com")),
        state=MainDialogStates.greeting,
        getter=get_data_from_user
    ),
    Window(
        Const("""Отлично!
Теперь отправь мне своё фото!)

Не бойся, оно мне нужно только для того, чтобы я мог перенести твои черты лица на сгенерированного персонажа.)"""),
        SwitchTo(Const("Объясните поподробнее..."), id='explanation', state=MainDialogStates.explanation),
        MessageInput(upload_photo),
        state=MainDialogStates.photo_upload,
        getter=get_data_from_user
    ),
    Window(
        Const("Кажется, это не фотография...\nПришли мне фотографию своего лица!)"),
        MessageInput(upload_photo),
        state=MainDialogStates.photo_not_uploaded,
        getter=get_data_from_user
    ),
    Window(
        Const("""Мы используем нейросетевые технологии для того, чтобы сначала сгенерировать аватарку твой мечты✨, а потом добавить в неё твои уникальные черты лица. 
Больше мы никак не используем твоё замечательное лицо и обязуемся сохранить его в тайне)"""),
        SwitchTo(Const("◀️ Назад"), id='back', state=MainDialogStates.photo_upload),
        state=MainDialogStates.explanation,
        getter=get_data_from_user
    ),
    Window(
        Const("А теперь опиши аватарку своей мечты.✨"),
        MessageInput(process_description),
        state=MainDialogStates.description,
        getter=get_data_from_user
    ),
    Window(
        Const("Кажется, это не описание аватарки твоей мечты✨...\nОпиши её и отправь описание мне!"),
        MessageInput(process_description),
        state=MainDialogStates.description_not_provided,
        getter=get_data_from_user
    ),
    Window(
        Format("""Супер!
Генерируем аватарку твоей мечты ✨...

Осталось примерно {remaining_seconds} секунд."""),
        Progress("progress", 10, filled='🟩'),
        state=MainDialogStates.generating,
        getter=get_progress
    ),
    Window(
        Const("""Лови свою новую аватарку мечты!✨"""),
        DynamicMedia("final_image"),
        Button(Const("Сгенерировать снова"), id='try_again', on_click=process_description__with_already_set_text),
        SwitchTo(Const("Сгенерировать новую аватарку"), id='new_ava', state=MainDialogStates.description),
        SwitchTo(Const("Загрузить другую фотографию"), id='upload_face', state=MainDialogStates.photo_upload),
        state=MainDialogStates.generated_success,
        getter=get_final_image
    ),
    Window(
        Format("""Не получилось сделать новую аватарку мечты...✨ {error}"""),
        Button(Const("Сгенерировать снова"), id='try_again', on_click=process_description__with_already_set_text),
        SwitchTo(Const("Сгенерировать новую аватарку"), id='new_ava', state=MainDialogStates.description),
        SwitchTo(Const("Загрузить другую фотографию"), id='upload_face', state=MainDialogStates.photo_upload),
        state=MainDialogStates.generated_failure,
        getter=get_error
    ),
)
