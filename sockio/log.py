import sys
import structlog
import logging
from sockio.config import config


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=config.log_level.upper()
    )
    
    if config.log_format.lower() == "json":
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def make_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


configure_logging()


class WebSocketLogger:
    def __init__(self, name: str = "websocket"):
        self.logger = make_logger(name)
    
    def connection_opened(self, websocket_id: str, user_id: str = None, ip_address: str = None):
        self.logger.info(
            "WebSocket connection opened",
            websocket_id=websocket_id,
            user_id=user_id,
            ip_address=ip_address
        )
    
    def connection_closed(self, websocket_id: str, user_id: str = None, code: int = None):
        self.logger.info(
            "WebSocket connection closed",
            websocket_id=websocket_id,
            user_id=user_id,
            close_code=code
        )
    
    def message_received(self, websocket_id: str, user_id: str, message_type: str, size: int):
        self.logger.debug(
            "WebSocket message received",
            websocket_id=websocket_id,
            user_id=user_id,
            message_type=message_type,
            message_size=size
        )
    
    def message_sent(self, websocket_id: str, user_id: str, message_type: str, size: int):
        self.logger.debug(
            "WebSocket message sent",
            websocket_id=websocket_id,
            user_id=user_id,
            message_type=message_type,
            message_size=size
        )
    
    def authentication_success(self, websocket_id: str, user_id: str, username: str):
        self.logger.info(
            "WebSocket authentication successful",
            websocket_id=websocket_id,
            user_id=user_id,
            username=username
        )
    
    def authentication_failed(self, websocket_id: str, reason: str):
        self.logger.warning(
            "WebSocket authentication failed",
            websocket_id=websocket_id,
            reason=reason
        )
    
    def error(self, websocket_id: str, error: str, user_id: str = None):
        self.logger.error(
            "WebSocket error",
            websocket_id=websocket_id,
            user_id=user_id,
            error=error
        )


class ChatLogger:
    def __init__(self, name: str = "chat"):
        self.logger = make_logger(name)
    
    def message_sent(self, user_id: str, conversation_id: str, message_id: str, message_type: str):
        self.logger.info(
            "Message sent",
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            message_type=message_type
        )
    
    def message_edited(self, user_id: str, message_id: str):
        self.logger.info(
            "Message edited",
            user_id=user_id,
            message_id=message_id
        )
    
    def message_deleted(self, user_id: str, message_id: str):
        self.logger.info(
            "Message deleted",
            user_id=user_id,
            message_id=message_id
        )
    
    def conversation_created(self, user_id: str, conversation_id: str, conversation_type: str):
        self.logger.info(
            "Conversation created",
            user_id=user_id,
            conversation_id=conversation_id,
            conversation_type=conversation_type
        )
    
    def user_joined_conversation(self, user_id: str, conversation_id: str, role: str):
        self.logger.info(
            "User joined conversation",
            user_id=user_id,
            conversation_id=conversation_id,
            role=role
        )
    
    def user_left_conversation(self, user_id: str, conversation_id: str):
        self.logger.info(
            "User left conversation",
            user_id=user_id,
            conversation_id=conversation_id
        )
    
    def contact_request_sent(self, from_user_id: str, to_user_id: str):
        self.logger.info(
            "Contact request sent",
            from_user_id=from_user_id,
            to_user_id=to_user_id
        )
    
    def contact_request_accepted(self, from_user_id: str, to_user_id: str):
        self.logger.info(
            "Contact request accepted",
            from_user_id=from_user_id,
            to_user_id=to_user_id
        )
    
    def file_uploaded(self, user_id: str, filename: str, file_size: int, mime_type: str):
        self.logger.info(
            "File uploaded",
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type
        )


