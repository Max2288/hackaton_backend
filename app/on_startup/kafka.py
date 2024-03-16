from aiokafka.producer import AIOKafkaProducer

from app.core.config import Config
from app.db import kafka


async def create_producer() -> None:
    kafka.producer = AIOKafkaProducer(bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS)

    await kafka.producer.start()

    kafka.partitions = list(await kafka.producer.partitions_for(Config.KAFKA_TOPIC))