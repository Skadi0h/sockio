from datetime import datetime, timezone
from typing import Optional, Any
from sockio.models import (
    User,
    Conversation,
    ConversationParticipant,
    Message,
    ConversationType,
    MessageType,
    ParticipantRole
)
from sockio.log import make_logger, ChatLogger

logger = make_logger("sockio.chat_service")
chat_logger = ChatLogger()


class ChatService:
    
    async def create_direct_conversation(self, user1_id: str, user2_id: str) -> Optional[Conversation]:
        try:
            user1 = await User.get(user1_id)
            user2 = await User.get(user2_id)
            
            if not user1 or not user2:
                return None
            
            existing_conv = await self._find_direct_conversation(user1_id, user2_id)
            if existing_conv:
                return existing_conv
            
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
            
            chat_logger.conversation_created(user1_id, str(conversation.id), "direct")
            
            return conversation
        
        except Exception as e:
            logger.error("Error creating direct conversation", exc_info=e)
            return None
    
    async def create_group_conversation(self, creator_id: str, name: str, description: str = None,
                                        participant_ids: list[str] = None) -> Optional[Conversation]:
        try:
            creator = await User.get(creator_id)
            if not creator:
                return None
            
            conversation = Conversation(
                type=ConversationType.GROUP,
                name=name,
                description=description,
                created_by=creator
            )
            await conversation.insert()
            
            creator_participant = ConversationParticipant(
                conversation_id=conversation,
                user_id=creator,
                role=ParticipantRole.OWNER
            )
            await creator_participant.insert()
            
            if participant_ids:
                for user_id in participant_ids:
                    if user_id != creator_id:
                        user = await User.get(user_id)
                        if user:
                            participant = ConversationParticipant(
                                conversation_id=conversation,
                                user_id=user,
                                role=ParticipantRole.MEMBER
                            )
                            await participant.insert()
            
            chat_logger.conversation_created(creator_id, str(conversation.id), "group")
            
            return conversation
        
        except Exception as e:
            logger.error("Error creating group conversation", error=str(e))
            return None
    
    async def send_message(self, sender_id: str, conversation_id: str, content: str, message_type: str = "text",
                           reply_to_id: str = None) -> Optional[Message]:
        try:
            sender = await User.get(sender_id)
            conversation = await Conversation.get(conversation_id)
            
            if not sender or not conversation:
                return None
            
            participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == sender_id,
                ConversationParticipant.left_at== None
            )
            
            if not participant:
                return None
            
            message = Message(
                conversation_id=conversation,
                sender_id=sender,
                content=content,
                message_type=MessageType(message_type),
                reply_to_id=reply_to_id
            )
            
            await message.insert()
            
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save()
            
            chat_logger.message_sent(sender_id, conversation_id, str(message.id), message_type)
            
            return message
        
        except Exception as e:
            logger.error("Error sending message", error=str(e))
            return None
    
    async def edit_message(self, user_id: str, message_id: str, new_content: str) -> bool:
        try:
            message = await Message.get(message_id)
            if not message or str(message.sender_id) != user_id:
                return False
            
            message.content = new_content
            message.edited_at = datetime.now(timezone.utc)
            await message.save()
            
            chat_logger.message_edited(user_id, message_id)
            
            return True
        
        except Exception as e:
            logger.error("Error editing message", error=str(e))
            return False
    
    async def delete_message(self, user_id: str, message_id: str) -> bool:
        try:
            message = await Message.get(message_id)
            if not message or str(message.sender_id) != user_id:
                return False
            
            message.deleted_at = datetime.now(timezone.utc)
            await message.save()
            
            chat_logger.message_deleted(user_id, message_id)
            
            return True
        
        except Exception as e:
            logger.error("Error deleting message", error=str(e))
            return False
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> list[Message]:
        try:
            messages = await Message.find(
                Message.conversation_id == conversation_id,
                Message.deleted_at == None
            ).sort(-Message.created_at).skip(offset).limit(limit).to_list()
            
            return list(reversed(messages))
        
        except Exception as e:
            logger.error("Error getting conversation messages", error=str(e))
            return []
    
    async def get_user_conversations(self, user_id: str) -> list[dict[str, Any]]:
        # try:
        participants = await ConversationParticipant.find(
            ConversationParticipant.user_id.id == user_id,
            ConversationParticipant.left_at == None
        ).to_list()
        logger.info('PARTICIPANTS', participants=participants)
        
        conversations = []
        for participant in participants:
            conversation = await Conversation.get(participant.conversation_id.ref.id)
            if conversation and conversation.is_active:
                conv_data = conversation.to_dict()

                last_message = await Message.find(
                    Message.conversation_id == str(conversation.id),
                    Message.deleted_at == None
                ).sort(-Message.created_at).limit(1).to_list()

                if last_message:
                    conv_data['last_message'] = last_message[0].to_dict()

                if conversation.type == ConversationType.DIRECT:
                    other_participant = await ConversationParticipant.find_one(
                        ConversationParticipant.conversation_id == str(conversation.id),
                        ConversationParticipant.user_id != user_id,
                        ConversationParticipant.left_at == None
                    )
                    if other_participant:
                        other_user = await User.get(other_participant.user_id.ref.id)
                        if other_user:
                            conv_data['other_user'] = other_user.to_dict()
            
                conversations.append(conv_data)
        
        return sorted(conversations, key=lambda x: x.get('updated_at', ''), reverse=True)
        
        # except Exception as e:
        #     logger.error("Error getting user conversations", error=str(e))
        #     return []
    
    async def add_participant_to_group(self, admin_user_id: str, conversation_id: str, user_id: str) -> bool:
        try:
            admin_participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == admin_user_id,
                ConversationParticipant.left_at == None
            )
            
            if not admin_participant or admin_participant.role not in [ParticipantRole.ADMIN, ParticipantRole.OWNER]:
                return False
            
            existing_participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.left_at == None
            )
            
            if existing_participant:
                return False
            
            user = await User.get(user_id)
            conversation = await Conversation.get(conversation_id)
            
            if not user or not conversation:
                return False
            
            participant = ConversationParticipant(
                conversation_id=conversation,
                user_id=user,
                role=ParticipantRole.MEMBER
            )
            await participant.insert()
            
            chat_logger.user_joined_conversation(user_id, conversation_id, "member")
            
            return True
        
        except Exception as e:
            logger.error("Error adding participant to group", error=str(e))
            return False
    
    async def remove_participant_from_group(self, admin_user_id: str, conversation_id: str, user_id: str) -> bool:
        try:
            admin_participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == admin_user_id,
                ConversationParticipant.left_at == None
            )
            
            if not admin_participant or admin_participant.role not in [ParticipantRole.ADMIN, ParticipantRole.OWNER]:
                return False
            
            participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.left_at == None
            )
            
            if not participant:
                return False
            
            participant.left_at = datetime.now(timezone.utc)
            await participant.save()
            
            chat_logger.user_left_conversation(user_id, conversation_id)
            
            return True
        
        except Exception as e:
            logger.error("Error removing participant from group", error=str(e))
            return False
    
    async def leave_conversation(self, user_id: str, conversation_id: str) -> bool:
        try:
            participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.left_at == None
            )
            
            if not participant:
                return False
            
            participant.left_at = datetime.now(timezone.utc)
            await participant.save()
            
            chat_logger.user_left_conversation(user_id, conversation_id)
            
            return True
        
        except Exception as e:
            logger.error("Error leaving conversation", error=str(e))
            return False
    
    async def mark_messages_as_read(self, user_id: str, conversation_id: str, message_id: str) -> bool:
        try:
            participant = await ConversationParticipant.find_one(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.left_at == None
            )
            
            if not participant:
                return False
            
            participant.last_read_message_id = message_id
            await participant.save()
            
            return True
        
        except Exception as e:
            logger.error("Error marking messages as read", error=str(e))
            return False
    
    async def get_conversation_participants(self, conversation_id: str) -> list[dict[str, Any]]:
        try:
            participants = await ConversationParticipant.find(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.left_at == None
            ).to_list()
            
            result = []
            for participant in participants:
                user = await User.get(participant.user_id)
                if user:
                    participant_data = participant.to_dict()
                    participant_data['user'] = user.to_dict()
                    result.append(participant_data)
            
            return result
        
        except Exception as e:
            logger.error("Error getting conversation participants", error=str(e))
            return []
    
    async def _find_direct_conversation(self, user1_id: str, user2_id: str) -> Optional[Conversation]:
        participants1 = await ConversationParticipant.find(
            ConversationParticipant.user_id == user1_id,
            ConversationParticipant.left_at == None
        ).to_list()
        
        participants2 = await ConversationParticipant.find(
            ConversationParticipant.user_id == user2_id,
            ConversationParticipant.left_at == None
        ).to_list()
        
        for p1 in participants1:
            for p2 in participants2:
                if p1.conversation_id == p2.conversation_id:
                    conv = await Conversation.get(p1.conversation_id)
                    if conv and conv.type == ConversationType.DIRECT:
                        return conv
        
        return None


chat_service = ChatService()
