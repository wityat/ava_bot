import os
from dataclasses import dataclass

import aiohttp
import asyncio
import logging
import json

from aiogram_dialog import DialogManager
from aiogram_dialog.manager.bg_manager import BgManager


@dataclass
class RetryConfig:
    count_retries = 10
    delay_between_retries = 10


class KandinskyAPI:

    def __init__(self, api_key=None, secret_key=None, retry_config=RetryConfig(), host='https://api-key.fusionbrain.ai/'):
        self.host = host
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key or os.getenv("KANDINSKY_API_KEY", "")}',
            'X-Secret': f'Secret {secret_key or os.getenv("KANDINSKY_SECRET_KEY", "")}',
        }
        self.session = None
        self.retry_config = retry_config

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def get_model(self):
        await self._ensure_session()
        async with self.session.get(self.host + 'key/api/v1/models', headers=self.AUTH_HEADERS) as response:
            data = await response.json()
            try:
                return data[0]['id']
            except KeyError:
                logging.error(data)

    async def create_generation_job(self, prompt, model, images=1, width=1024, height=1024):
        await self._ensure_session()
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }
        data = aiohttp.FormData()
        data.add_field('model_id',
                       str(model))
        data.add_field('params',
                       json.dumps(params),
                       content_type='application/json')

        async with self.session.post(self.host + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, data=data) as response:
            data = await response.json()
            try:
                return data['uuid']
            except KeyError:
                logging.error(data)

    async def check_status_generation_job(self, request_id):
        await self._ensure_session()
        async with self.session.get(self.host + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS) as response:
            data = await response.json()
            if data['status'] == 'DONE':
                return data['images']

    async def generate(self, query, manager: BgManager=None, progress_data=None):
        model_id = await self.get_model()
        job_id = await self.create_generation_job(query, model_id)

        if job_id:
            counter_retries = 0
            while counter_retries < self.retry_config.count_retries:
                result = await self.check_status_generation_job(job_id)
                if result:
                    return result
                else:
                    await asyncio.sleep(self.retry_config.delay_between_retries)
                    progress_data["remaining_seconds"] = progress_data["remaining_seconds"] - self.retry_config.delay_between_retries
                    progress_data["progress"] = (counter_retries+1) * 100 / self.retry_config.count_retries
                    if manager:
                        await manager.update(progress_data)
                counter_retries += 1
        else:
            return {'error': 'No job_id provided or generating failed'}


# Example usage:
async def main():
    from dotenv import load_dotenv

    load_dotenv()
    api = KandinskyAPI()
    try:
        images = await api.generate("A futuristic city skyline at sunset")
        print(images)
    finally:
        await api.close_session()


if __name__ == '__main__':
    asyncio.run(main())

