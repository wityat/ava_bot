import base64
import logging
import io
from io import BytesIO

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram_dialog import Dialog, DialogManager, Window, setup_dialogs
from aiogram_dialog.widgets.kbd import Button, Row, Url, Select, Next
from aiogram_dialog.widgets.text import Const, Format
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.filters import CommandStart
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import ChatEvent
from aiogram.filters.state import StatesGroup, State
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram.fsm.storage.memory import MemoryStorage
import numpy as np

from face_swapper import FaceSwapper
from kandinsky import Text2ImageAPI
import requests
import cv2
from dotenv import load_dotenv

load_dotenv()
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
kandinsky_api = Text2ImageAPI()
face_swapper_api = FaceSwapper()


class DialogStates(StatesGroup):
    greeting = State()  # Пользователь принимает правила
    photo_upload = State()  # Загрузка фото пользователя
    face_selection = State()  # Выбор лица на фото
    description = State()  # Ввод описания для фотографии


logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token='6964084500:AAGpZd1VZVPwqZOp0JfdoHnc9h9f_uRWacU')
dp = Dispatcher()


async def start(m: types.Message, dialog: Dialog, manager: DialogManager):
    await dialog.next()


async def upload_photo(message: types.Message, dialog: Dialog, manager: DialogManager):
    if message.photo:
        # Загрузка изображения в память
        image_data: io.BytesIO = await bot.download(message.photo[-1])
        image_bytes = image_data.getvalue()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = [((x, y, w, h), i+1) for i, (x, y, w, h) in enumerate(face_cascade.detectMultiScale(gray, 1.1, 4))]
        for (x, y, w, h), i in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, f"Face {i}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Сохранение изображения в BytesIO
        is_success, buffer = cv2.imencode(".jpg", image)
        io_buf = BytesIO(buffer)

        # Отправка изображения
        io_buf.seek(0)
        photo = types.BufferedInputFile(io_buf.read(), filename="image.jpg")
        sent_message = await bot.send_photo(message.chat.id, photo=photo)
        file_id = sent_message.photo[-1].file_id
        photo_with_faces = MediaAttachment(ContentType.PHOTO, file_id=MediaId(file_id))
        manager.current_context().dialog_data["faces"] = faces
        manager.current_context().dialog_data["photo_with_faces"] = photo_with_faces
        manager.current_context().dialog_data["face_photo"] = message.photo[-1]
    await manager.switch_to(state=DialogStates.face_selection)


async def face_selected(c: ChatEvent, button: Button, manager: DialogManager, item_id: str):
    manager.current_context().dialog_data["selected_face_id"] = item_id
    await manager.switch_to(state=DialogStates.description)


async def user_accept_rules(c: ChatEvent, button: Button, manager: DialogManager):
    await manager.switch_to(state=DialogStates.photo_upload)


async def process_description(message: types.Message, dialog: Dialog, manager: DialogManager):
    images = await kandinsky_api.generate(message.text)
    photo = base64.b64decode(images[0])
    # selected_face_id = manager.current_context().dialog_data.get("selected_face_id", '')
    # faces = manager.current_context().dialog_data.get("faces", '')
    # x, y, w, h = faces[int(selected_face_id)-1][0]
    # face_position = [{"width": int(w), "height": int(h), "x": int(x), "y": int(y)}]
    face_photo = manager.current_context().dialog_data.get("face_photo")
    face_photo_data: io.BytesIO = await bot.download(face_photo.file_id)
    urls = await face_swapper_api.swap(photo, face_photo_data.getvalue())
    sent_message = await bot.send_photo(message.chat.id, photo=urls[0])
    # await manager.dialog().next(state=DialogStates.greeting)  # Возвращаемся в начальное состояние


async def get_data_from_user(dialog_manager: DialogManager, **kwargs):
    user_data = dialog_manager.current_context().dialog_data
    print(user_data.get("faces"))
    return {
        "selected_face": user_data.get("selected_face"),
        "photo_with_faces": user_data.get("photo_with_faces"),
        "faces": user_data.get("faces"),
        # Добавьте другие данные, если это необходимо
    }


dialog = Dialog(
    Window(
        Const("Привет! Я бот, который поможет тебе сделать новую аватарку в соцсетях, классное фото для резюме в "
              "деловом стиле или просто поможет сделать интересные фотографии с твоим лицом. Для того, чтобы начать "
              "нажми кнопку принять, чтобы принять правила пользования ботом и начать создавать картинки."),
        Row(Button(Const("Принять"), id="accept", on_click=user_accept_rules), Url(Const("Правила"), Const("https://example.com"))),
        state=DialogStates.greeting,
        getter=get_data_from_user
    ),
    Window(
        Const("Загрузи фото лица"),
        MessageInput(upload_photo),
        state=DialogStates.photo_upload,
        getter=get_data_from_user
    ),
    Window(
        DynamicMedia("photo_with_faces"),
        Const("Выбери лицо"),
        Select(
            Format("Face {item[1]}"),  # E.g `✓ Apple (1/4)`
            id="s_faces",
            item_id_getter=lambda item: item[1],
            items="faces",
            on_click=face_selected,
        ),
        Next(Const("Пропустить")),
        state=DialogStates.face_selection,
        getter=get_data_from_user
    ),
    Window(
        Const("Красивое))) Теперь опиши фотографию..."),
        MessageInput(process_description),
        state=DialogStates.description,
        getter=get_data_from_user
    ),
)

dp.include_router(dialog)
setup_dialogs(dp)


@dp.message(CommandStart())
async def cmd_start(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogStates.greeting)


if __name__ == '__main__':
    dp.run_polling(bot)
