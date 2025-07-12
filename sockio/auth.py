"""
Authentication and session management for the WebSocket chat server.
"""

import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, validator
from sockio.config import config
from sqlalchemy import select, update
from sockio.db import db_manager, AsyncSession
from sockio.models import User, UserSession, UserStatus
from sockio.log import make_logger

logger = make_logger("sockio.auth")


class UserRegistrationRequest(BaseModel):
    """User registration request model."""
    username: str
    email: EmailStr
    password: str
    display_name: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if len(v) < 1 or len(v) > 100:
            raise ValueError('Display name must be between 1 and 100 characters')
        return v.strip()


class UserLoginRequest(BaseModel):
    """User login request model."""
    username: str
    password: str


class AuthResponse(BaseModel):
    """Authentication response model."""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    session_token: Optional[str] = None


class AuthenticationManager:
    """Manages user authentication and sessions."""
    
    def __init__(self):
        self.secret_key = config.jwt_secret_key
        self.algorithm = config.jwt_algorithm
        self.token_expiration = timedelta(hours=config.jwt_expiration_hours)
        self.session_expiration = timedelta(hours=config.session_expiration_hours)
    
    async def register_user(self, registration_data: UserRegistrationRequest) -> AuthResponse:
        """Register a new user."""
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(select(User).where(User.username == registration_data.username))
                if result.scalar_one_or_none():
                    return AuthResponse(success=False, message="Username already exists")

                result = await session.execute(select(User).where(User.email == registration_data.email))
                if result.scalar_one_or_none():
                    return AuthResponse(success=False, message="Email already exists")

                user = User(
                    username=registration_data.username,
                    email=registration_data.email,
                    display_name=registration_data.display_name,
                    status=UserStatus.OFFLINE,
                )
                user.set_password(registration_data.password)
                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info(
                    "User registered successfully",
                    user_id=str(user.id),
                    username=user.username,
                )

                return AuthResponse(success=True, message="User registered successfully", user=user.to_dict())
            
        except Exception as e:
            logger.error("User registration failed", error=str(e))
            return AuthResponse(
                success=False,
                message="Registration failed"
            )
    
    async def login_user(self, login_data: UserLoginRequest, ip_address: str = None, user_agent: str = None) -> AuthResponse:
        """Authenticate user and create session."""
        try:
            async with db_manager.get_session() as session_db:
                result = await session_db.execute(select(User).where(User.username == login_data.username.lower()))
                user = result.scalar_one_or_none()
                if not user or not user.check_password(login_data.password):
                    return AuthResponse(success=False, message="Invalid username or password")

                session = await self.create_session(session_db, user, ip_address, user_agent)

                user.status = UserStatus.ONLINE
                user.last_seen = datetime.now(timezone.utc)
                await session_db.commit()

                logger.info("User logged in successfully", user_id=str(user.id), username=user.username)

                return AuthResponse(success=True, message="Login successful", user=user.to_dict(), session_token=session.session_token)
            
        except Exception as e:
            logger.error("User login failed", error=str(e))
            return AuthResponse(
                success=False,
                message="Login failed"
            )
    
    async def logout_user(self, session_token: str) -> AuthResponse:
        """Logout user and invalidate session."""
        try:
            async with db_manager.get_session() as session_db:
                result = await session_db.execute(
                    select(UserSession).where(
                        UserSession.session_token == session_token,
                        UserSession.is_active.is_(True),
                    )
                )
                session_obj = result.scalar_one_or_none()

                if session_obj:
                    session_obj.is_active = False
                    result_user = await session_db.execute(
                        select(User).where(User.id == session_obj.user_id)
                    )
                    user = result_user.scalar_one_or_none()
                    if user:
                        user.status = UserStatus.OFFLINE
                        user.last_seen = datetime.now(timezone.utc)

                    await session_db.commit()

                    logger.info(
                        "User logged out successfully", user_id=str(session_obj.user_id)
                    )

                return AuthResponse(success=True, message="Logout successful")
            
        except Exception as e:
            logger.error("User logout failed", error=e)
            return AuthResponse(
                success=False,
                message="Logout failed"
            )
    
    async def create_session(self, db: AsyncSession, user: User, ip_address: str | None = None, user_agent: str | None = None) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            user_id=user.id,
            session_token=UserSession.generate_token(),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + self.session_expiration,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    async def verify_session(self, session_token: str) -> Optional[User]:
        """Verify session token and return user."""
        try:
            async with db_manager.get_session() as session_db:
                result = await session_db.execute(
                    select(UserSession).where(
                        UserSession.session_token == session_token,
                        UserSession.is_active.is_(True),
                    )
                )
                session_obj = result.scalar_one_or_none()

                if not session_obj:
                    return None

                if session_obj.is_expired():
                    session_obj.is_active = False
                    await session_db.commit()
                    return None

                user_result = await session_db.execute(select(User).where(User.id == session_obj.user_id))
                return user_result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Session verification failed", error=str(e))
            return None
    
    async def authenticate_websocket(self, token: str) -> Optional[User]:
        """Authenticate WebSocket connection using token."""
        user = await self.verify_session(token)
        if user:
            return user
        
        return None
    
    async def update_websocket_session(self, session_token: str, websocket_id: str) -> bool:
        """Update session with WebSocket ID."""
        try:
            async with db_manager.get_session() as session_db:
                result = await session_db.execute(
                    select(UserSession).where(
                        UserSession.session_token == session_token,
                        UserSession.is_active.is_(True),
                    )
                )
                session_obj = result.scalar_one_or_none()
                if session_obj:
                    session_obj.websocket_id = websocket_id
                    await session_db.commit()
                    return True

                return False
            
        except Exception as e:
            logger.error("Failed to update WebSocket session", error=str(e))
            return False
    
    async def get_user_sessions(self, user_id: str) -> list[UserSession]:
        """Get all active sessions for a user."""
        try:
            sessions = await UserSession.find(
                UserSession.user_id.id == user_id,
                UserSession.is_active == True
            ).to_list()
            
            return sessions
            
        except Exception as e:
            logger.error("Failed to get user sessions", error=str(e))
            return []
    
    async def invalidate_user_sessions(self, user_id: str, except_session: str = None) -> int:
        """Invalidate all sessions for a user except the specified one."""
        try:
            query = UserSession.find(
                UserSession.user_id.id == user_id,
                UserSession.is_active == True
            )
            
            if except_session:
                query = query.find(UserSession.session_token != except_session)
            
            sessions = await query.to_list()
            
            count = 0
            for session in sessions:
                session.is_active = False
                await session.save()
                count += 1
            
            logger.info("Invalidated user sessions", user_id=user_id, count=count)
            return count
            
        except Exception as e:
            logger.error("Failed to invalidate user sessions", error=str(e))
            return 0


class PasswordManager:
    """Utility class for password operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a password reset token."""
        import secrets
        return secrets.token_urlsafe(32)


# Global authentication manager instance
auth_manager = AuthenticationManager()


# Utility functions
async def require_auth(token: str) -> Optional[User]:
    """Decorator helper to require authentication."""
    return await auth_manager.authenticate_websocket(token)


async def get_current_user(session_token: str) -> Optional[User]:
    """Get current user from session token."""
    return await auth_manager.verify_session(session_token)

