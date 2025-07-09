"""
WebSocket connection manager for handling user sessions and presence.
"""

import asyncio
import uuid
from typing import Dict, Set, Optional, List
from datetime import datetime, timezone, timedelta
from socketify import WebSocket
from sockio.models import User, UserStatus, UserSession
from sockio.auth import auth_manager
from sockio.log import WebSocketLogger, make_logger

logger = make_logger("sockio.connection_manager")
ws_logger = WebSocketLogger()


class WebSocketConnection:
    """Represents a WebSocket connection with user context."""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user: Optional[User] = None
        self.session_token: Optional[str] = None
        self.authenticated = False
        self.connected_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.subscribed_conversations: Set[str] = set()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
    
    def is_authenticated(self) -> bool:
        """Check if connection is authenticated."""
        return self.authenticated and self.user is not None
    
    def get_user_id(self) -> Optional[str]:
        """Get user ID if authenticated."""
        return str(self.user.id) if self.user else None


class ConnectionManager:
    """Manages WebSocket connections and user presence."""
    
    def __init__(self):
        # Map connection_id -> WebSocketConnection
        self.connections: Dict[str, WebSocketConnection] = {}
        
        # Map user_id -> Set[connection_id] (for multiple connections per user)
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Map conversation_id -> Set[connection_id] (for room subscriptions)
        self.conversation_subscribers: Dict[str, Set[str]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    def generate_connection_id(self) -> str:
        """Generate a unique connection ID."""
        return str(uuid.uuid4())
    
    async def add_connection(self, websocket: WebSocket) -> str:
        """Add a new WebSocket connection."""
        connection_id = self.generate_connection_id()
        
        async with self._lock:
            connection = WebSocketConnection(websocket, connection_id)
            self.connections[connection_id] = connection
        
        ws_logger.connection_opened(connection_id)
        logger.info("WebSocket connection added", connection_id=connection_id)
        
        return connection_id
    
    async def remove_connection(self, connection_id: str, close_code: int = None):
        """Remove a WebSocket connection."""
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            # Remove from user connections
            if connection.user:
                user_id = str(connection.user.id)
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                        
                        # Update user status to offline if no more connections
                        await self._update_user_status(connection.user, UserStatus.OFFLINE)
            
            # Remove from conversation subscriptions
            for conversation_id in connection.subscribed_conversations:
                if conversation_id in self.conversation_subscribers:
                    self.conversation_subscribers[conversation_id].discard(connection_id)
                    if not self.conversation_subscribers[conversation_id]:
                        del self.conversation_subscribers[conversation_id]
            
            # Remove connection
            del self.connections[connection_id]
        
        ws_logger.connection_closed(
            connection_id, 
            connection.get_user_id() if connection else None, 
            close_code
        )
        logger.info("WebSocket connection removed", connection_id=connection_id)
    
    async def authenticate_connection(self, connection_id: str, token: str) -> bool:
        """Authenticate a WebSocket connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        # Authenticate user
        user = await auth_manager.authenticate_websocket(token)
        if not user:
            ws_logger.authentication_failed(connection_id, "Invalid token")
            return False
        
        async with self._lock:
            # Set user and authentication status
            connection.user = user
            connection.session_token = token
            connection.authenticated = True
            
            # Add to user connections
            user_id = str(user.id)
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Update WebSocket ID in session if it's a session token
            await auth_manager.update_websocket_session(token, connection_id)
        
        # Update user status to online
        await self._update_user_status(user, UserStatus.ONLINE)
        
        ws_logger.authentication_success(connection_id, str(user.id), user.username)
        logger.info("WebSocket connection authenticated", 
                   connection_id=connection_id, 
                   user_id=str(user.id), 
                   username=user.username)
        
        return True
    
    async def subscribe_to_conversation(self, connection_id: str, conversation_id: str) -> bool:
        """Subscribe a connection to a conversation."""
        connection = self.connections.get(connection_id)
        if not connection or not connection.is_authenticated():
            return False
        
        async with self._lock:
            # Add to conversation subscribers
            if conversation_id not in self.conversation_subscribers:
                self.conversation_subscribers[conversation_id] = set()
            self.conversation_subscribers[conversation_id].add(connection_id)
            
            # Add to connection's subscriptions
            connection.subscribed_conversations.add(conversation_id)
        
        logger.info("Connection subscribed to conversation", 
                   connection_id=connection_id, 
                   conversation_id=conversation_id,
                   user_id=connection.get_user_id())
        
        return True
    
    async def unsubscribe_from_conversation(self, connection_id: str, conversation_id: str) -> bool:
        """Unsubscribe a connection from a conversation."""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        async with self._lock:
            # Remove from conversation subscribers
            if conversation_id in self.conversation_subscribers:
                self.conversation_subscribers[conversation_id].discard(connection_id)
                if not self.conversation_subscribers[conversation_id]:
                    del self.conversation_subscribers[conversation_id]
            
            # Remove from connection's subscriptions
            connection.subscribed_conversations.discard(conversation_id)
        
        logger.info("Connection unsubscribed from conversation", 
                   connection_id=connection_id, 
                   conversation_id=conversation_id,
                   user_id=connection.get_user_id())
        
        return True
    
    async def send_to_connection(self, connection_id: str, message: bytes) -> bool:
        """Send message to a specific connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        try:
            connection.websocket.send(message)
            connection.update_activity()
            
            ws_logger.message_sent(
                connection_id, 
                connection.get_user_id() or "anonymous", 
                "unknown", 
                len(message)
            )
            
            return True
        except Exception as e:
            logger.error("Failed to send message to connection", 
                        connection_id=connection_id, 
                        error=str(e))
            return False
    
    async def send_to_user(self, user_id: str, message: bytes) -> int:
        """Send message to all connections of a user."""
        connection_ids = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for connection_id in connection_ids.copy():  # Copy to avoid modification during iteration
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_conversation(self, conversation_id: str, message: bytes, exclude_user_id: str = None) -> int:
        """Send message to all subscribers of a conversation."""
        connection_ids = self.conversation_subscribers.get(conversation_id, set())
        sent_count = 0
        
        for connection_id in connection_ids.copy():  # Copy to avoid modification during iteration
            connection = self.connections.get(connection_id)
            if connection and connection.is_authenticated():
                # Skip excluded user
                if exclude_user_id and connection.get_user_id() == exclude_user_id:
                    continue
                
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: bytes, authenticated_only: bool = True) -> int:
        """Broadcast message to all connections."""
        sent_count = 0
        
        for connection_id, connection in self.connections.items():
            if authenticated_only and not connection.is_authenticated():
                continue
            
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def get_user_status(self, user_id: str) -> UserStatus:
        """Get user's current status."""
        if user_id in self.user_connections:
            return UserStatus.ONLINE
        
        # Check database for last known status
        try:
            user = await User.get(user_id)
            return user.status if user else UserStatus.OFFLINE
        except:
            return UserStatus.OFFLINE
    
    async def update_user_status(self, user_id: str, status: UserStatus) -> bool:
        """Update user's status."""
        try:
            user = await User.get(user_id)
            if user:
                await self._update_user_status(user, status)
                return True
            return False
        except Exception as e:
            logger.error("Failed to update user status", user_id=user_id, error=str(e))
            return False
    
    async def _update_user_status(self, user: User, status: UserStatus):
        """Internal method to update user status."""
        user.status = status
        user.last_seen = datetime.now(timezone.utc)
        await user.save()
        
        logger.info("User status updated", 
                   user_id=str(user.id), 
                   username=user.username, 
                   status=status)
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """Get connection information."""
        connection = self.connections.get(connection_id)
        if not connection:
            return None
        
        return {
            'connection_id': connection_id,
            'user_id': connection.get_user_id(),
            'authenticated': connection.is_authenticated(),
            'connected_at': connection.connected_at.isoformat(),
            'last_activity': connection.last_activity.isoformat(),
            'subscribed_conversations': list(connection.subscribed_conversations)
        }
    
    def get_stats(self) -> Dict:
        """Get connection manager statistics."""
        total_connections = len(self.connections)
        authenticated_connections = sum(1 for conn in self.connections.values() if conn.is_authenticated())
        unique_users = len(self.user_connections)
        active_conversations = len(self.conversation_subscribers)
        
        return {
            'total_connections': total_connections,
            'authenticated_connections': authenticated_connections,
            'anonymous_connections': total_connections - authenticated_connections,
            'unique_users': unique_users,
            'active_conversations': active_conversations
        }
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """Clean up inactive connections."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        inactive_connections = []
        
        for connection_id, connection in self.connections.items():
            if connection.last_activity < cutoff_time:
                inactive_connections.append(connection_id)
        
        for connection_id in inactive_connections:
            await self.remove_connection(connection_id)
        
        if inactive_connections:
            logger.info("Cleaned up inactive connections", count=len(inactive_connections))
        
        return len(inactive_connections)


# Global connection manager instance
connection_manager = ConnectionManager()

