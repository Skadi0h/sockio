"""
Database initialization and connection management for MongoDB with Beanie ODM.
"""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from sockio.log import make_logger
from sockio.config import config
from sockio.models import (
    User,
    Conversation,
    ConversationParticipant,
    Message,
    Contact,
    FileAttachment,
    UserSession,
    MessageReadReceipt,
    TypingIndicator,
)

logger = make_logger('sockio.db')

class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
    
    async def connect(self) -> None:
        """Connect to MongoDB and initialize Beanie."""
        try:
            # Create Motor client
            self.client = AsyncIOMotorClient(config.mongodb_url)
            
            # Get database
            self.database = self.client[config.mongodb_database]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB", url=config.mongodb_url)
            
            # Initialize Beanie with document models
            await init_beanie(
                database=self.database,
                document_models=[
                    User,
                    Conversation,
                    ConversationParticipant,
                    Message,
                    Contact,
                    FileAttachment,
                    UserSession,
                    MessageReadReceipt,
                    TypingIndicator,
                ]
            )
            logger.info("Beanie ODM initialized successfully")
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    async def drop_database(self) -> None:
        """Drop the entire database (use with caution!)."""
        if self.client:
            await self.client.drop_database(config.mongodb_database)
            print(f"Dropped database: {config.mongodb_database}")
    
    async def create_indexes(self) -> None:
        """Create additional custom indexes if needed."""
        try:
            # Additional indexes can be created here if needed
            # The models already define their own indexes
            pass
        except Exception as e:
            print(f"Error creating indexes: {e}")
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            if not self.client:
                return False
            
            # Ping the database
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def init_db() -> None:
    """Initialize database connection."""
    await db_manager.connect()
    await db_manager.create_indexes()


async def close_db() -> None:
    """Close database connection."""
    await db_manager.disconnect()


async def get_database():
    """Get database instance."""
    return db_manager.database


async def get_client():
    """Get MongoDB client instance."""
    return db_manager.client


# Utility functions for common database operations
async def create_default_admin_user() -> Optional[User]:
    """Create a default admin user if no users exist."""
    try:
        # Check if any users exist
        user_count = await User.count()
        if user_count > 0:
            return None
        
        # Create default admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            display_name="Administrator",
            status="offline"
        )
        admin_user.set_password("admin123")
        
        await admin_user.insert()
        print("Created default admin user (username: admin, password: admin123)")
        return admin_user
        
    except Exception as e:
        print(f"Error creating default admin user: {e}")
        return None


async def cleanup_expired_sessions() -> int:
    """Clean up expired user sessions."""
    try:
        from datetime import datetime, timezone
        
        # Find and delete expired sessions
        expired_sessions = await UserSession.find(
            UserSession.expires_at < datetime.now(timezone.utc)
        ).to_list()
        
        count = len(expired_sessions)
        if count > 0:
            for session in expired_sessions:
                await session.delete()
            print(f"Cleaned up {count} expired sessions")
        
        return count
        
    except Exception as e:
        print(f"Error cleaning up expired sessions: {e}")
        return 0


async def cleanup_old_typing_indicators() -> int:
    """Clean up old typing indicators (older than 30 seconds)."""
    try:
        from datetime import datetime, timezone, timedelta
        
        # Find and delete old typing indicators
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        old_indicators = await TypingIndicator.find(
            TypingIndicator.started_at < cutoff_time
        ).to_list()
        
        count = len(old_indicators)
        if count > 0:
            for indicator in old_indicators:
                await indicator.delete()
        
        return count
        
    except Exception as e:
        print(f"Error cleaning up typing indicators: {e}")
        return 0



async def periodic_cleanup():
    """Run periodic cleanup tasks."""
    while True:
        try:
            await cleanup_expired_sessions()
            await cleanup_old_typing_indicators()
            
            # Sleep for 5 minutes before next cleanup
            await asyncio.sleep(300)
            
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

