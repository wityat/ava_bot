import json
import logging
import random
from copy import copy
from dataclasses import dataclass

import aiohttp
import asyncio

from aiogram_dialog import DialogManager
from aiogram_dialog.manager.bg_manager import BgManager


@dataclass
class RetryConfig:
    count_retries = 10
    delay_between_retries = 10


class FaceSwapper:
    def __init__(self, retry_config=RetryConfig()):
        self.hosts = ["https://access1.faceswapper.ai",
                      "https://access3.faceswapper.ai",
                      "https://access4.faceswapper.ai"]
        self.retry_config = retry_config

    async def swap(self, file_to_replace_face, file_with_face, face_position=None,
                   manager: BgManager = None,  progress_data=None):
        upload_result = await self.upload_files(file_to_replace_face, file_with_face, face_position)
        retries_max_count = max(self.retry_config.count_retries, int(progress_data["remaining_seconds"]/self.retry_config.delay_between_retries))
        start_progress = copy(progress_data["progress"])
        if (code := upload_result.get('code', '')) != '':
            retry_counter = 0
            while retry_counter < retries_max_count:
                status_result = await self.check_status(code)
                if status_result.get('status') == 'success':
                    return status_result["downloadUrls"]
                else:
                    await asyncio.sleep(self.retry_config.delay_between_retries)
                    progress_data["remaining_seconds"] = progress_data["remaining_seconds"] - self.retry_config.delay_between_retries
                    progress_data["progress"] = start_progress + ((retry_counter+1) * (100-start_progress) / retries_max_count)
                    await manager.update(progress_data)
                retry_counter += 1
        else:
            return {'error': 'No code provided or upload failed'}

    async def upload_files(self, file_to_replace_face, file_with_face, face_position=None):
        link = "/api/FaceSwapper/UploadByFile"
        data = aiohttp.FormData()
        # image to add face
        data.add_field('file',
                       file_to_replace_face,
                       content_type='multipart/form-data')
        # face
        data.add_field('fileother',
                       file_with_face,
                       content_type='multipart/form-data')
        if face_position:
            data.add_field('position',
                           json.dumps(face_position))

        # Выбираем случайный хост для балансировки нагрузки
        host = random.choice(self.hosts)

        async with aiohttp.ClientSession() as session:
            async with session.post(host + link, data=data, ssl=False) as response:
                status = response.status
                if status == 200:
                    response = await response.json()
                    return response["data"]
                else:
                    return {'status': "failure", 'message': await response.text()}

    async def check_status(self, code):
        link = "/api/FaceSwapper/CheckStatus"
        data = {"code": code}

        # Выбираем случайный хост для балансировки нагрузки
        host = random.choice(self.hosts)

        async with aiohttp.ClientSession() as session:
            async with session.post(host + link, json=data, ssl=False) as response:
                status = response.status
                if status == 200:
                    # Возвращаем JSON-ответ, если статус запроса 200 OK
                    response = await response.json()
                    return response["data"]
                else:
                    # Возвращаем статус запроса и текст ответа в случае ошибки
                    return {'status': "failure", 'message': await response.text()}


async def main():
    from dotenv import load_dotenv

    load_dotenv()
    api = FaceSwapper()
    with open("img.jpg", "rb") as f:
        with open("img_1.png", "rb") as face:
            images = await api.swap(f, face)
            print(images)
