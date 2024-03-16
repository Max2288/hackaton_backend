import os
import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4


@asynccontextmanager
async def async_tmp_image_file():
    """Генерирует уникальный путь до временного файла, при выходе удаляет файл."""
    os.makedirs('tmp', exist_ok=True)
    fp = f"tmp/{uuid4()}"
    try:
        yield fp
    finally:
        if os.path.exists(fp):
            os.remove(fp)
