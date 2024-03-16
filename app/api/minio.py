import json
from datetime import time

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.log_route import LogRoute
from app.core.exceptions import UserNotFoundException, OrderNotFoundException
from app.db import crud, session
from app.db.crud import get_user_by_username, create_order, get_orders
from app.db.kafka import get_producer, get_partition
from app.db.models import OrderEnum
from app.schemas.schema import UserEntity, UserInfo, UserResponse, OrderInfo
from miniopy_async import Minio
import io
import msgpack
from app.core.config import Config
from app.services.files import tmp_image_file

router = APIRouter(route_class=LogRoute)


client = Minio(
    "host.docker.internal:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)


@router.post("/load", status_code=status.HTTP_200_OK)
async def load_to_minio(username: str,file: UploadFile = File(...), db: AsyncSession = Depends(session.get_db)):
    try:
        user = await get_user_by_username(db, username)

        if user is None:
            raise UserNotFoundException()
        with tmp_image_file() as f:
            f.write(file.read())
            logger.info(f.filepath)
        await client.fput_object(
            bucket_name=Config.BUCKET_NAME,
            object_name=f"files/{user.id}",
            file_path=file,
        )
        order_data = OrderInfo(
            user = user.id,
            status = OrderEnum.pending
        )
        order = await create_order(db, order_data)

        if order is None:
            raise OrderNotFoundException("Order not created")
        producer = get_producer()
        kafka_data = {"order_id": order.id, "file_path": "minio_filename"}
        value = msgpack.packb(kafka_data)
        await producer.send_and_wait(
            topic=Config.KAFKA_TOPIC,
            value=value,
            partition=get_partition(),
        )
        return ORJSONResponse(
            {"message": "User"}
        )
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        logger.error(f"Произошла ошибка во время получения пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
