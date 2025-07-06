from datetime import datetime, timedelta
from typing import Optional
from pydantic import Field, BaseModel
from beanie import Document
from pymongo import IndexModel


class User(BaseModel):
    """Embedded user information in messages."""
    user_id: str = Field(..., description="Unique user identifier")
    username: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")


class Message(Document):
    """Chat message document."""
    
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    room: str = Field(default="room", description="Chat room name")
    user: Optional[User] = Field(None, description="User who sent the message")
    message_type: str = Field(default="text", description="Type of message (text, image, etc.)")
    edited: bool = Field(default=False, description="Whether message was edited")
    edited_at: Optional[datetime] = Field(None, description="When message was edited")
    
    class Settings:
        name = "messages"
        indexes = [
            IndexModel("timestamp"),
            IndexModel("room"),
            IndexModel("user.user_id"),
            IndexModel([("room", 1), ("timestamp", -1)]),  # Compound index for room messages
        ]
    
    @classmethod
    async def get_recent_messages(cls, room: str, limit: int = 50):
        """Get recent messages for a room."""
        return await cls.find(
            cls.room == room
        ).sort(-cls.timestamp).limit(limit).to_list()
    
    @classmethod
    async def get_messages_after(cls, room: str, timestamp: datetime, limit: int = 50):
        """Get messages after a specific timestamp."""
        return await cls.find(
            cls.room == room,
            cls.timestamp > timestamp
        ).sort(cls.timestamp).limit(limit).to_list()


class Room(Document):
    """Chat room document."""
    
    name: str = Field(..., description="Room name")
    description: Optional[str] = Field(None, description="Room description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Room creation time")
    is_private: bool = Field(default=False, description="Whether room is private")
    max_users: Optional[int] = Field(None, description="Maximum number of users")
    
    class Settings:
        name = "rooms"
        indexes = [
            IndexModel("name", unique=True),
            IndexModel("created_at"),
        ]


class Connection(Document):
    """Track active WebSocket connections."""
    
    user_id: str = Field(..., description="User ID")
    room: str = Field(..., description="Room name")
    connected_at: datetime = Field(default_factory=datetime.utcnow, description="Connection timestamp")
    last_seen: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    
    class Settings:
        name = "connections"
        indexes = [
            IndexModel("user_id"),
            IndexModel("room"),
            IndexModel("last_seen"),
            IndexModel([("user_id", 1), ("room", 1)], unique=True),  # One connection per user per room
        ]
    
    async def update_last_seen(self):
        """Update the last seen timestamp."""
        self.last_seen = datetime.utcnow()
        await self.save()
    
    @classmethod
    async def get_active_users(cls, room: str, timeout_minutes: int = 5):
        """Get users active in a room within the timeout period."""
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        return await cls.find(
            cls.room == room,
            cls.last_seen > cutoff_time
        ).to_list()