"""
Configuration module for the WebSocket chat server.
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config(BaseSettings):
    """Application configuration."""
    
    # Server settings
    ws_host: str = Field(default="0.0.0.0", env="WS_HOST")
    ws_port: int = Field(default=8000, env="WS_PORT")
    ws_max_payload: int = Field(default=16 * 1024 * 1024, env="WS_MAX_PAYLOAD")  # 16MB
    ws_idle_timeout: int = Field(default=300, env="WS_IDLE_TIMEOUT")  # 5 minutes
    ws_room_name: str = Field(default="general", env="WS_ROOM_NAME")
    
    # MongoDB settings
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="chat_app", env="MONGODB_DATABASE")
    
    # Authentication settings
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    session_expiration_hours: int = Field(default=168, env="SESSION_EXPIRATION_HOURS")  # 7 days
    
    # File upload settings
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    allowed_file_types: List[str] = Field(
        default=[
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "video/mp4", "video/webm", "video/quicktime",
            "audio/mpeg", "audio/wav", "audio/ogg",
            "application/pdf", "text/plain",
            "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="text", env="LOG_FORMAT")  # json or text
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Rate limiting
    rate_limit_messages_per_minute: int = Field(default=60, env="RATE_LIMIT_MESSAGES_PER_MINUTE")
    rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # Typing indicator settings
    typing_timeout_seconds: int = Field(default=5, env="TYPING_TIMEOUT_SECONDS")
    
    # Message settings
    max_message_length: int = Field(default=4000, env="MAX_MESSAGE_LENGTH")
    message_history_limit: int = Field(default=100, env="MESSAGE_HISTORY_LIMIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def ws_url(self) -> str:
        """Get WebSocket URL."""
        return f"ws://{self.ws_host}:{self.ws_port}"
    
    @property
    def http_url(self) -> str:
        """Get HTTP URL."""
        return f"http://{self.ws_host}:{self.ws_port}"
    
    def ensure_upload_dir(self) -> None:
        """Ensure upload directory exists."""
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Create subdirectories for different file types
        subdirs = ["images", "videos", "audio", "documents", "others"]
        for subdir in subdirs:
            os.makedirs(os.path.join(self.upload_dir, subdir), exist_ok=True)


# Global configuration instance
config = Config()
