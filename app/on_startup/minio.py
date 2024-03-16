from miniopy_async import Minio

from app.core.config import Config


async def create_bucket():
    client = Minio(
        "host.docker.internal:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    result = await client.bucket_exists(Config.BUCKET_NAME)
    if not result:
        print("Creating bucket")
        await client.make_bucket(Config.BUCKET_NAME)
    else:
        print("Bucket exist")