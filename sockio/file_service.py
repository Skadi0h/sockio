import os
import uuid
import aiofiles
from datetime import datetime, timezone
from typing import Optional, List
from sockio.models import FileAttachment, Message
from sockio.config import config
from sockio.log import make_logger

logger = make_logger("sockio.file_service")


class FileService:
    def __init__(self):
        self.upload_dir = config.upload_dir
        self.max_file_size = config.max_file_size
        self.allowed_types = config.allowed_file_types
    
    async def save_file(self, file_data: bytes, filename: str, mime_type: str, user_id: str) -> Optional[FileAttachment]:
        try:
            if len(file_data) > self.max_file_size:
                logger.error(f"File too large: {len(file_data)} bytes")
                return None
            
            if not self._is_allowed_type(mime_type):
                logger.error(f"File type not allowed: {mime_type}")
                return None
            
            file_id = str(uuid.uuid4())
            file_extension = self._get_file_extension(filename)
            safe_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            os.makedirs(self.upload_dir, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            attachment = FileAttachment(
                id=file_id,
                filename=filename,
                file_path=file_path,
                file_size=len(file_data),
                mime_type=mime_type,
                uploaded_by=user_id,
                uploaded_at=datetime.now(timezone.utc)
            )
            
            await attachment.save()
            logger.info(f"File saved: {filename} ({len(file_data)} bytes)")
            return attachment
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None
    
    async def get_file(self, file_id: str) -> Optional[FileAttachment]:
        try:
            return await FileAttachment.get(file_id)
        except Exception as e:
            logger.error(f"Error getting file: {e}")
            return None
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        try:
            attachment = await FileAttachment.get(file_id)
            if not attachment:
                return False
            
            if attachment.uploaded_by != user_id:
                logger.error(f"User {user_id} not authorized to delete file {file_id}")
                return False
            
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
            
            await attachment.delete()
            logger.info(f"File deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def get_file_data(self, file_path: str) -> Optional[bytes]:
        try:
            if not os.path.exists(file_path):
                return None
            
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None
    
    def _is_allowed_type(self, mime_type: str) -> bool:
        if not self.allowed_types:
            return True
        return mime_type in self.allowed_types
    
    def _get_file_extension(self, filename: str) -> str:
        return os.path.splitext(filename)[1].lower()
    
    async def get_message_attachments(self, message_id: str) -> List[FileAttachment]:
        try:
            message = await Message.get(message_id)
            if not message or not message.attachments:
                return []
            
            attachments = []
            for attachment_id in message.attachments:
                attachment = await FileAttachment.get(attachment_id)
                if attachment:
                    attachments.append(attachment)
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error getting message attachments: {e}")
            return []


file_service = FileService()

