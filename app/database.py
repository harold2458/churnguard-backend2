from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings


client = AsyncIOMotorClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=5000
)

database: AsyncIOMotorDatabase = client[settings.mongo_db_name]


async def ping_database() -> None:
    await database.command("ping")


def get_database() -> AsyncIOMotorDatabase:
    return database
