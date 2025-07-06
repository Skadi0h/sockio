from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie


from sockio.models import Message
from sockio.config import config
from sockio.log import make_logger

logger = make_logger(__name__)


async def init_db() -> None:
    """Initialize database connection and Beanie ODM."""
    try:
        client = AsyncIOMotorClient(config.mongo_url)
        
        await client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {config.mongo_host}:{config.mongo_port}")
    
        await init_beanie(
            database=client[config.mongo_database],
            document_models=[Message]
        )
        
        logger.info(f"Beanie initialized with database: {config.mongo_database}")
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db_connection(client: AsyncIOMotorClient) -> None:
    """Close database connection."""
    try:
        client.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")