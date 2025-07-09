
from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId
from sockio.models import Message, Conversation, User, FileAttachment
from sockio.log import make_logger

logger = make_logger("sockio.message_history_service")


class MessageHistoryService:
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: int = 50, 
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            conversation = await Conversation.get(conversation_id)
            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return []
            
            if not await self._user_has_access(conversation, user_id):
                logger.error(f"User {user_id} has no access to conversation {conversation_id}")
                return []
            
            query = {"conversation_id": PydanticObjectId(conversation_id), "is_deleted": False}
            
            if before:
                try:
                    before_message = await Message.get(before)
                    if before_message:
                        query["created_at"] = {"$lt": before_message.created_at}
                except Exception as e:
                    logger.warning(f"Invalid before parameter: {before}")
            
            messages = await Message.find(query).sort(-Message.created_at).limit(limit).to_list()
            
            messages_data = []
            for message in messages:
                message_data = await self._format_message(message)
                messages_data.append(message_data)
            
            messages_data.reverse()
            return messages_data
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []
    
    async def get_message_by_id(self, message_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            message = await Message.get(message_id)
            if not message:
                return None
            
            conversation = await Conversation.get(str(message.conversation_id))
            if not conversation or not await self._user_has_access(conversation, user_id):
                return None
            
            return await self._format_message(message)
            
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return None
    
    async def search_messages(
        self, 
        conversation_id: str, 
        user_id: str, 
        query: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            conversation = await Conversation.get(conversation_id)
            if not conversation or not await self._user_has_access(conversation, user_id):
                return []
            
            search_filter = {
                "conversation_id": PydanticObjectId(conversation_id),
                "is_deleted": False,
                "content": {"$regex": query, "$options": "i"}
            }
            
            messages = await Message.find(search_filter).sort(-Message.created_at).limit(limit).to_list()
            
            messages_data = []
            for message in messages:
                message_data = await self._format_message(message)
                messages_data.append(message_data)
            
            return messages_data
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    async def get_user_message_history(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        try:
            user_conversations = await Conversation.find(
                {"participants.user_id": PydanticObjectId(user_id)}
            ).to_list()
            
            conversation_ids = [str(conv.id) for conv in user_conversations]
            
            messages = await Message.find({
                "conversation_id": {"$in": [PydanticObjectId(cid) for cid in conversation_ids]},
                "is_deleted": False
            }).sort(-Message.created_at).limit(limit).to_list()
            
            messages_data = []
            for message in messages:
                message_data = await self._format_message(message)
                messages_data.append(message_data)
            
            return messages_data
            
        except Exception as e:
            logger.error(f"Error getting user message history: {e}")
            return []
    
    async def get_conversation_stats(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            conversation = await Conversation.get(conversation_id)
            if not conversation or not await self._user_has_access(conversation, user_id):
                return None
            
            total_messages = await Message.find({
                "conversation_id": PydanticObjectId(conversation_id),
                "is_deleted": False
            }).count()
            
            total_attachments = await Message.find({
                "conversation_id": PydanticObjectId(conversation_id),
                "is_deleted": False,
                "attachments": {"$exists": True, "$ne": []}
            }).count()
            
            first_message = await Message.find({
                "conversation_id": PydanticObjectId(conversation_id),
                "is_deleted": False
            }).sort(Message.created_at).first_or_none()
            
            last_message = await Message.find({
                "conversation_id": PydanticObjectId(conversation_id),
                "is_deleted": False
            }).sort(-Message.created_at).first_or_none()
            
            return {
                "conversation_id": conversation_id,
                "total_messages": total_messages,
                "total_attachments": total_attachments,
                "first_message_at": first_message.created_at if first_message else None,
                "last_message_at": last_message.created_at if last_message else None
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return None
    
    async def _user_has_access(self, conversation: Conversation, user_id: str) -> bool:
        try:
            user_obj_id = PydanticObjectId(user_id)
            for participant in conversation.participants:
                if participant.user_id == user_obj_id and participant.left_at is None:
                    return True
            return False
        except Exception:
            return False
    
    async def _format_message(self, message: Message) -> Dict[str, Any]:
        try:
            message_data = {
                "id": str(message.id),
                "conversation_id": str(message.conversation_id),
                "sender_id": str(message.sender_id),
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at.isoformat(),
                "updated_at": message.updated_at.isoformat() if message.updated_at else None,
                "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                "is_deleted": message.is_deleted,
                "attachments": []
            }
            
            if message.sender_id:
                sender = await User.get(str(message.sender_id))
                if sender:
                    message_data["sender"] = {
                        "id": str(sender.id),
                        "username": sender.username,
                        "display_name": sender.display_name
                    }
            
            if message.attachments:
                for attachment_id in message.attachments:
                    try:
                        attachment = await FileAttachment.get(str(attachment_id))
                        if attachment:
                            message_data["attachments"].append({
                                "id": str(attachment.id),
                                "filename": attachment.filename,
                                "file_size": attachment.file_size,
                                "mime_type": attachment.mime_type,
                                "uploaded_at": attachment.uploaded_at.isoformat()
                            })
                    except Exception as e:
                        logger.warning(f"Error loading attachment {attachment_id}: {e}")
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return {}


message_history_service = MessageHistoryService()

