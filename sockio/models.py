from datetime import datetime, timezone
from typing import Any
from enum import Enum
from pydantic import Field, EmailStr
from beanie import Document, Indexed, Link, before_event, Update
from pymongo import IndexModel, ASCENDING, DESCENDING
from werkzeug.security import generate_password_hash, check_password_hash
import uuid


class UserStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class ConversationType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    VOICE = "voice"


class ContactStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DECLINED = "declined"


class ParticipantRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    password_hash: str = Field(default='')
    display_name: str
    avatar_url: str | None = None
    status: UserStatus = UserStatus.OFFLINE
    bio: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"
        indexes = [
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING)]),
        ]
    
    @before_event(Update)
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        data = {
            'id': str(self.id),
            'username': self.username,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'status': self.status,
            'bio': self.bio,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }
        if include_sensitive:
            data['email'] = self.email
        return data


class Conversation(Document):
    type: ConversationType
    name: str | None = None  # NULL for direct chats
    description: str | None = None
    avatar_url: str | None = None
    created_by: Link[User] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    class Settings:
        name = "conversations"
        indexes = [
            IndexModel([("type", ASCENDING)]),
            IndexModel([("created_by", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("updated_at", DESCENDING)]),
        ]
    
    @before_event(Update)
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict[str, Any]:
        data = {
            'id': str(self.id),
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'avatar_url': self.avatar_url,
            'created_by': str(self.created_by.id) if self.created_by else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }
        return data


class ConversationParticipant(Document):

    conversation_id: Link[Conversation]
    user_id: Link[User]
    role: ParticipantRole = ParticipantRole.MEMBER
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    left_at: datetime | None = None
    last_read_message_id: str | None = None  # Reference to Message ID
    is_muted: bool = False
    
    class Settings:
        name = "conversation_participants"
        indexes = [
            IndexModel([("conversation_id", ASCENDING), ("user_id", ASCENDING)], unique=True),
            IndexModel([("conversation_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("left_at", ASCENDING)]),
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id.id),
            'user_id': str(self.user_id.id),
            'role': self.role,
            'joined_at': self.joined_at.isoformat(),
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'last_read_message_id': self.last_read_message_id,
            'is_muted': self.is_muted
        }


class Message(Document):
    conversation_id: Link[Conversation]
    sender_id: Link[User] | None = None
    content: str | None = None
    message_type: MessageType = MessageType.TEXT
    reply_to_id: str | None = None  # Reference to another Message ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    is_pinned: bool = False
    
    class Settings:
        name = "messages"
        indexes = [
            IndexModel([("conversation_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("sender_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("message_type", ASCENDING)]),
            IndexModel([("deleted_at", ASCENDING)]),
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id.id),
            'sender_id': str(self.sender_id.id) if self.sender_id else None,
            'content': self.content,
            'message_type': self.message_type,
            'reply_to_id': self.reply_to_id,
            'created_at': self.created_at.isoformat(),
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'is_pinned': self.is_pinned
        }


class Contact(Document):
    user_id: Link[User]
    contact_user_id: Link[User]
    status: ContactStatus = ContactStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "contacts"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("contact_user_id", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("contact_user_id", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
        ]
    
    @before_event(Update)
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id.id),
            'contact_user_id': str(self.contact_user_id.id),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class FileAttachment(Document):
    message_id: Link[Message]
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    thumbnail_path: str | None = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "file_attachments"
        indexes = [
            IndexModel([("message_id", ASCENDING)]),
            IndexModel([("mime_type", ASCENDING)]),
            IndexModel([("uploaded_at", DESCENDING)]),
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'message_id': str(self.message_id.id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'thumbnail_path': self.thumbnail_path,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class UserSession(Document):
    user_id: Link[User]
    session_token: Indexed(str, unique=True)
    websocket_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_active: bool = True
    
    class Settings:
        name = "user_sessions"
        indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("session_token", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)]),
            IndexModel([("is_active", ASCENDING)]),
        ]
    
    @classmethod
    def generate_token(cls) -> str:
        return str(uuid.uuid4())
    
    def is_expired(self) -> bool:
        # todo: make aware utc
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict[str, Any]:

        return {
            'id': str(self.id),
            'user_id': str(self.user_id.id),
            'session_token': self.session_token,
            'websocket_id': self.websocket_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active
        }


class MessageReadReceipt(Document):
    message_id: Link[Message]
    user_id: Link[User]
    read_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "message_read_receipts"
        indexes = [
            IndexModel([("message_id", ASCENDING), ("user_id", ASCENDING)], unique=True),
            IndexModel([("message_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("read_at", DESCENDING)]),
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'message_id': str(self.message_id.id),
            'user_id': str(self.user_id.id),
            'read_at': self.read_at.isoformat()
        }


class TypingIndicator(Document):
    conversation_id: Link[Conversation]
    user_id: Link[User]
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "typing_indicators"
        indexes = [
            IndexModel([("conversation_id", ASCENDING), ("user_id", ASCENDING)], unique=True),
            IndexModel([("conversation_id", ASCENDING)]),
            IndexModel([("started_at", ASCENDING)]),
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id.id),
            'user_id': str(self.user_id.id),
            'started_at': self.started_at.isoformat()
        }


# Database initialization function
async def init_beanie_db(database_url: str = "mongodb://localhost:27017", database_name: str = "chat_app"):

    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    
    client = AsyncIOMotorClient(database_url)
    
    await init_beanie(
        database=client[database_name],
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
    
    return client



async def create_direct_conversation(user1_id: str, user2_id: str) -> Conversation:

    user1 = await User.get(user1_id)
    user2 = await User.get(user2_id)
    
    if not user1 or not user2:
        raise ValueError("One or both users not found")

    participants1 = await ConversationParticipant.find(
        ConversationParticipant.user_id == user1.id,
        ConversationParticipant.left_at == None
    ).to_list()
    
    participants2 = await ConversationParticipant.find(
        ConversationParticipant.user_id == user2.id,
        ConversationParticipant.left_at == None
    ).to_list()
    

    common_conversations = []
    for p1 in participants1:
        for p2 in participants2:
            if p1.conversation_id == p2.conversation_id:
                conv = await Conversation.get(p1.conversation_id.id)
                if conv and conv.type == ConversationType.DIRECT:
                    common_conversations.append(conv)
    
    if common_conversations:
        return common_conversations[0]
    

    conversation = Conversation(
        type=ConversationType.DIRECT,
        created_by=user1
    )
    await conversation.insert()
    

    participant1 = ConversationParticipant(
        conversation_id=conversation,
        user_id=user1,
        role=ParticipantRole.MEMBER
    )
    participant2 = ConversationParticipant(
        conversation_id=conversation,
        user_id=user2,
        role=ParticipantRole.MEMBER
    )
    
    await participant1.insert()
    await participant2.insert()
    
    return conversation


async def get_user_conversations(user_id: str) -> list[Conversation]:
    user = await User.get(user_id)
    if not user:
        return []
    
    participants = await ConversationParticipant.find(
        ConversationParticipant.user_id == user.id,
        ConversationParticipant.left_at == None
    ).to_list()
    
    conversations = []
    for participant in participants:
        conversation = await Conversation.get(participant.conversation_id.id)
        if conversation and conversation.is_active:
            conversations.append(conversation)
    
    return conversations


async def get_conversation_messages(conversation_id: str, limit: int = 50, offset: int = 0) -> list[Message]:

    conversation = await Conversation.get(conversation_id)
    if not conversation:
        return []
    
    messages = await Message.find(
        Message.conversation_id == conversation.id,
        Message.deleted_at is None
    ).sort(-Message.created_at).skip(offset).limit(limit).to_list()
    
    return list(reversed(messages)) 

