import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from config import settings

logger = logging.getLogger("transport_severa.db")

class Database:
    client: AsyncIOMotorClient = None
    db = None
    is_connected: bool = False
    _fallback_store: dict = {}

db_instance = Database()

async def connect_to_mongo():
    logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URI.split('@')[-1] if '@' in settings.MONGODB_URI else settings.MONGODB_URI}")
    try:
        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2500
        )
        # Test connection ping
        await db_instance.client.admin.command('ping')
        db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
        db_instance.is_connected = True
        logger.info(f"Successfully connected to MongoDB database '{settings.MONGODB_DB_NAME}'")
        
        # Create indexes according to datalogical model
        await setup_indexes()
    except Exception as e:
        logger.warning(f"Could not connect to MongoDB ({e}). Activating embedded in-memory fallback mode for reliable testing/demo.")
        db_instance.is_connected = False
        db_instance.db = None

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

async def setup_indexes():
    if not db_instance.is_connected:
        return
    try:
        # stations
        await db_instance.db.stations.create_index("code", unique=True)
        await db_instance.db.stations.create_index("city")
        # users
        await db_instance.db.users.create_index("username", unique=True)
        # trips
        await db_instance.db.trips.create_index([("schedule.departure_planned", 1), ("status", 1)])
        await db_instance.db.trips.create_index([("route.origin.city", 1), ("route.destination.city", 1)])
        await db_instance.db.trips.create_index("display_flags.is_hidden")
        # weather_logs
        await db_instance.db.weather_logs.create_index([("station_id", 1), ("timestamp", -1)])
        # audit_logs
        await db_instance.db.audit_logs.create_index([("timestamp", -1)])
        # subscriptions
        await db_instance.db.subscriptions.create_index([("recipient", 1), ("trip_id", 1)], unique=True)
        # notifications
        await db_instance.db.notifications.create_index("trip_id")
        logger.info("MongoDB indexes verified.")
    except Exception as e:
        logger.warning(f"Index creation notice: {e}")

def get_database():
    return db_instance
