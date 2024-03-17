import time

from aiokafka import AIOKafkaConsumer
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.log_route import LogRoute
from app.core.exceptions import UserNotFoundException, OrderNotFoundException
from app.db import session
from app.db.crud import get_user_by_username, create_order, get_order_by_id
from app.db.kafka import get_producer, get_partition
from app.db.models import OrderEnum
from app.schemas.schema import OrderInfo
from miniopy_async import Minio

import msgpack
from app.core.config import Config


router = APIRouter(route_class=LogRoute)


client = Minio("host.docker.internal:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)


@router.post("/load", status_code=status.HTTP_200_OK)
async def load_to_minio(
    username: str, order_name: str, file: UploadFile = File(...), db: AsyncSession = Depends(session.get_db)
):
    try:
        user = await get_user_by_username(db, username)

        if user is None:
            raise UserNotFoundException()

        file_length = len(await file.read())
        await file.seek(0)
        file_path = f"files/{user.id}.mp3"
        await client.put_object(bucket_name=Config.BUCKET_NAME, object_name=file_path, data=file, length=file_length)
        order_data = OrderInfo(user=user.id, status=OrderEnum.pending, name=order_name)
        order = await create_order(db, order_data)

        if order is None:
            raise OrderNotFoundException("Order not created")
        producer = get_producer()
        kafka_data = {"order_id": order.id, "file_path": file_path}
        value = msgpack.packb(kafka_data)
        await producer.send_and_wait(
            topic=Config.KAFKA_TOPIC,
            value=value,
            partition=get_partition(),
        )
        return ORJSONResponse({"message": "User"})
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        logger.error(f"Произошла ошибка во время получения пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/change", status_code=status.HTTP_200_OK)
async def change_status(
    user_id: int, status_name: OrderEnum, order_id: int, db: AsyncSession = Depends(session.get_db)
):
    try:
        order = await get_order_by_id(db, order_id)
        order_data = OrderInfo(user=user_id, status=status_name, name=order.name)
        order = await create_order(db, order_data)
        if order is None:
            raise OrderNotFoundException("Order not created")
        return ORJSONResponse({"order": order.id})
    except Exception as e:
        logger.error(f"Произошла ошибка во создания заказа: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

