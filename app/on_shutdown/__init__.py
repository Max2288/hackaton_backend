from app.db import kafka


async def stop_producer() -> None:
    await kafka.producer.stop()