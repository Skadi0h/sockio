from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Config(BaseSettings):
    """Application configuration using Pydantic Settings."""
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    

    mongo_host: str = Field(default="mongo", description="MongoDB host")
    mongo_port: int = Field(default=27017, description="MongoDB port")
    mongo_username: Optional[str] = Field(default=None, description="MongoDB username")
    mongo_password: Optional[str] = Field(default=None, description="MongoDB password")
    mongo_database: str = Field(default="my_database", description="MongoDB database name")
    

    ws_host: str = Field(default="localhost", description="WebSocket server host")
    ws_port: int = Field(default=3000, description="WebSocket server port")
    ws_max_payload: int = Field(
        default=1024 * 1024 * 1024,
        description="Maximum WebSocket payload size in bytes"
    )
    ws_idle_timeout: int = Field(
        default=900,
        description="WebSocket idle timeout in seconds"
    )
    ws_room_name: str = Field(default="room", description="Default WebSocket room name")
    

    log_level: str = Field(default="INFO", description="Logging level")
    
    @computed_field
    @property
    def mongo_url(self) -> str:
        """Build MongoDB connection URL from config."""
        if self.mongo_username and self.mongo_password:
            return f"mongodb://{self.mongo_username}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}"
        return f"mongodb://{self.mongo_host}:{self.mongo_port}"
    
    @computed_field
    @property
    def ws_url(self) -> str:
        """Build WebSocket server URL."""
        return f"ws://{self.ws_host}:{self.ws_port}"


# Global config instance
config = Config()
