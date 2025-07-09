import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from functools import singledispatchmethod
from pydantic import BaseModel

from sockio.models import User, Message
from sockio.connection_manager import connection_manager
from sockio.chat_service import chat_service
from sockio.contact_service import contact_service
from sockio.log import WebSocketLogger, ChatLogger, make_logger

logger = make_logger("sockio.message_handler")
ws_logger = WebSocketLogger()
chat_logger = ChatLogger()


class AuthMessage(BaseModel):
    token: str


class LogoutMessage(BaseModel):
    pass


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    message_type: str = 'text'
    reply_to_id: Optional[str] = None


class EditMessageRequest(BaseModel):
    message_id: str
    content: str


class DeleteMessageRequest(BaseModel):
    message_id: str


class MarkAsReadRequest(BaseModel):
    conversation_id: str
    message_id: str


class JoinConversationRequest(BaseModel):
    conversation_id: str


class LeaveConversationRequest(BaseModel):
    conversation_id: str


class CreateGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None
    participant_ids: list = []


class CreateDirectChatRequest(BaseModel):
    user_id: str


class AddParticipantsRequest(BaseModel):
    conversation_id: str
    user_ids: list


class RemoveParticipantRequest(BaseModel):
    conversation_id: str
    user_id: str


class TypingStartRequest(BaseModel):
    conversation_id: str


class TypingStopRequest(BaseModel):
    conversation_id: str


class UpdateStatusRequest(BaseModel):
    status: str


class GetConversationsRequest(BaseModel):
    pass


class GetMessagesRequest(BaseModel):
    conversation_id: str
    limit: int = 50
    offset: int = 0


class GetParticipantsRequest(BaseModel):
    conversation_id: str


class SendContactRequestRequest(BaseModel):
    user_id: str


class AcceptContactRequestRequest(BaseModel):
    contact_id: str


class DeclineContactRequestRequest(BaseModel):
    contact_id: str


class RemoveContactRequest(BaseModel):
    contact_user_id: str


class BlockUserRequest(BaseModel):
    user_id: str


class UnblockUserRequest(BaseModel):
    user_id: str


class GetContactsRequest(BaseModel):
    pass


class GetPendingRequestsRequest(BaseModel):
    pass


class GetBlockedUsersRequest(BaseModel):
    pass


class SearchUsersRequest(BaseModel):
    query: str
    limit: int = 20


class DispatchMessageHandler:
    def __init__(self):
        self.message_types = {
            'auth': AuthMessage,
            'logout': LogoutMessage,
            'send_message': SendMessageRequest,
            'edit_message': EditMessageRequest,
            'delete_message': DeleteMessageRequest,
            'mark_as_read': MarkAsReadRequest,
            'join_conversation': JoinConversationRequest,
            'leave_conversation': LeaveConversationRequest,
            'create_group': CreateGroupRequest,
            'create_direct_chat': CreateDirectChatRequest,
            'add_participants': AddParticipantsRequest,
            'remove_participant': RemoveParticipantRequest,
            'typing_start': TypingStartRequest,
            'typing_stop': TypingStopRequest,
            'update_status': UpdateStatusRequest,
            'get_conversations': GetConversationsRequest,
            'get_messages': GetMessagesRequest,
            'get_participants': GetParticipantsRequest,
            'send_contact_request': SendContactRequestRequest,
            'accept_contact_request': AcceptContactRequestRequest,
            'decline_contact_request': DeclineContactRequestRequest,
            'remove_contact': RemoveContactRequest,
            'block_user': BlockUserRequest,
            'unblock_user': UnblockUserRequest,
            'get_contacts': GetContactsRequest,
            'get_pending_requests': GetPendingRequestsRequest,
            'get_blocked_users': GetBlockedUsersRequest,
            'search_users': SearchUsersRequest,
        }
    
    async def handle_message(self, connection_id: str, message_data: bytes) -> None:
        try:
            message_str = message_data.decode('utf-8')
            message = json.loads(message_str)
            
            if not isinstance(message, dict) or 'type' not in message:
                await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "Invalid message format")
                return
            
            message_type = message.get('type')
            message_data = message.get('data', {})
            
            ws_logger.message_received(
                connection_id,
                self._get_user_id_from_connection(connection_id) or "anonymous",
                message_type,
                len(message_str)
            )
            
            model_class = self.message_types.get(message_type)
            if model_class is None:
                await self._send_error(connection_id, "UNKNOWN_MESSAGE_TYPE", f"Unknown message type: {message_type}")
                return
            
            try:
                request_model = model_class(**message_data)
                await self.handle_request(connection_id, request_model)
            except Exception as e:
                await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", f"Invalid message data: {str(e)}")
        
        except json.JSONDecodeError:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "Invalid JSON format")
        except Exception as e:
            logger.error("Error handling message", connection_id=connection_id, error=str(e))
            await self._send_error(connection_id, "SERVER_ERROR", "Internal server error")
    
    @singledispatchmethod
    async def handle_request(self, connection_id: str, request) -> None:
        await self._send_error(connection_id, "UNKNOWN_MESSAGE_TYPE", f"Unknown request type: {type(request)}")
    
    @handle_request.register
    async def _(self, connection_id: str, request: AuthMessage) -> None:
        success = await connection_manager.authenticate_connection(connection_id, request.token)
        if success:
            info = connection_manager.get_connection_info(connection_id)
            user = await User.get(info['user_id'])
            
            await self._send_message(connection_id, 'auth_success', {
                'user': user.to_dict()
            })
        else:
            await self._send_error(connection_id, "AUTHENTICATION_FAILED", "Invalid token")
    
    @handle_request.register
    async def _(self, connection_id: str, request: LogoutMessage) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        await self._send_message(connection_id, 'logout_success', {})
    
    @handle_request.register
    async def _(self, connection_id: str, request: SendMessageRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        message = await chat_service.send_message(
            str(user.id), request.conversation_id, request.content, request.message_type, request.reply_to_id
        )
        
        if message:
            await self._broadcast_to_conversation(request.conversation_id, 'new_message', {
                'message': {
                    'id': str(message.id),
                    'conversation_id': request.conversation_id,
                    'sender': user.to_dict(),
                    'content': request.content,
                    'message_type': request.message_type,
                    'reply_to_id': request.reply_to_id,
                    'created_at': message.created_at.isoformat(),
                    'attachments': []
                }
            })
        else:
            await self._send_error(connection_id, "PERMISSION_DENIED", "Cannot send message to this conversation")
    
    @handle_request.register
    async def _(self, connection_id: str, request: EditMessageRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        success = await chat_service.edit_message(str(user.id), request.message_id, request.content)
        
        if success:
            message = await Message.get(request.message_id)
            await self._broadcast_to_conversation(str(message.conversation_id.id), 'message_edited', {
                'message_id': request.message_id,
                'content': request.content,
                'edited_at': message.edited_at.isoformat()
            })
        else:
            await self._send_error(connection_id, "PERMISSION_DENIED", "Cannot edit this message")
    
    @handle_request.register
    async def _(self, connection_id: str, request: DeleteMessageRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        message = await Message.get(request.message_id)
        if not message:
            await self._send_error(connection_id, "MESSAGE_NOT_FOUND", "Message not found")
            return
        
        success = await chat_service.delete_message(str(user.id), request.message_id)
        
        if success:
            await self._broadcast_to_conversation(str(message.conversation_id.id), 'message_deleted', {
                'message_id': request.message_id,
                'deleted_at': datetime.now(timezone.utc).isoformat()
            })
        else:
            await self._send_error(connection_id, "PERMISSION_DENIED", "Cannot delete this message")
    
    @handle_request.register
    async def _(self, connection_id: str, request: MarkAsReadRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        success = await chat_service.mark_messages_as_read(str(user.id), request.conversation_id, request.message_id)
        
        if success:
            await self._send_message(connection_id, 'messages_marked_read', {
                'conversation_id': request.conversation_id,
                'message_id': request.message_id
            })
        else:
            await self._send_error(connection_id, "PERMISSION_DENIED", "Cannot mark messages as read")
    
    @handle_request.register
    async def _(self, connection_id: str, request: JoinConversationRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        success = await connection_manager.subscribe_to_conversation(connection_id, request.conversation_id)
        if success:
            await self._send_message(connection_id, 'conversation_joined', {
                'conversation_id': request.conversation_id
            })
        else:
            await self._send_error(connection_id, "SERVER_ERROR", "Failed to join conversation")
    
    @handle_request.register
    async def _(self, connection_id: str, request: LeaveConversationRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        success = await connection_manager.unsubscribe_from_conversation(connection_id, request.conversation_id)
        if success:
            await self._send_message(connection_id, 'conversation_left', {
                'conversation_id': request.conversation_id
            })
        else:
            await self._send_error(connection_id, "SERVER_ERROR", "Failed to leave conversation")
    
    @handle_request.register
    async def _(self, connection_id: str, request: CreateGroupRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        conversation = await chat_service.create_group_conversation(
            str(user.id), request.name, request.description, request.participant_ids
        )
        
        if conversation:
            participants = await chat_service.get_conversation_participants(str(conversation.id))
            
            await self._send_message(connection_id, 'group_created', {
                'conversation': {
                    'id': str(conversation.id),
                    'type': conversation.type,
                    'name': conversation.name,
                    'description': conversation.description,
                    'created_by': str(user.id),
                    'created_at': conversation.created_at.isoformat(),
                    'participants': participants
                }
            })
            
            for participant in participants:
                if participant['user']['id'] != str(user.id):
                    await connection_manager.send_to_user(participant['user']['id'], json.dumps({
                        'type': 'group_invitation',
                        'data': {
                            'conversation': conversation.to_dict(),
                            'invited_by': user.to_dict()
                        }
                    }).encode('utf-8'))
        else:
            await self._send_error(connection_id, "SERVER_ERROR", "Failed to create group")
    
    @handle_request.register
    async def _(self, connection_id: str, request: CreateDirectChatRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        conversation = await chat_service.create_direct_conversation(str(user.id), request.user_id)
        
        if conversation:
            other_user = await User.get(request.user_id)
            
            await self._send_message(connection_id, 'direct_chat_created', {
                'conversation': {
                    'id': str(conversation.id),
                    'type': conversation.type,
                    'created_at': conversation.created_at.isoformat(),
                    'other_user': other_user.to_dict() if other_user else None
                }
            })
        else:
            await self._send_error(connection_id, "SERVER_ERROR", "Failed to create direct chat")
    
    @handle_request.register
    async def _(self, connection_id: str, request: SendContactRequestRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        contact = await contact_service.send_contact_request(str(user.id), request.user_id)
        
        if contact:
            target_user = await User.get(request.user_id)
            
            await self._send_message(connection_id, 'contact_request_sent', {
                'contact': contact.to_dict(),
                'target_user': target_user.to_dict() if target_user else None
            })
            
            await connection_manager.send_to_user(request.user_id, json.dumps({
                'type': 'contact_request_received',
                'data': {
                    'contact': contact.to_dict(),
                    'from_user': user.to_dict()
                }
            }).encode('utf-8'))
        else:
            await self._send_error(connection_id, "CONTACT_REQUEST_FAILED", "Failed to send contact request")
    
    @handle_request.register
    async def _(self, connection_id: str, request: AcceptContactRequestRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        success = await contact_service.accept_contact_request(str(user.id), request.contact_id)
        
        if success:
            from sockio.models import Contact
            contact = await Contact.get(request.contact_id)
            from_user = await User.get(contact.user_id.id)
            
            await self._send_message(connection_id, 'contact_request_accepted', {
                'contact_id': request.contact_id,
                'contact_user': from_user.to_dict() if from_user else None
            })
            
            await connection_manager.send_to_user(str(contact.user_id.id), json.dumps({
                'type': 'contact_request_accepted',
                'data': {
                    'contact_id': request.contact_id,
                    'accepted_by': user.to_dict()
                }
            }).encode('utf-8'))
        else:
            await self._send_error(connection_id, "CONTACT_REQUEST_FAILED", "Failed to accept contact request")
    
    @handle_request.register
    async def _(self, connection_id: str, request: GetConversationsRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        conversations = await chat_service.get_user_conversations(str(user.id))
        
        await self._send_message(connection_id, 'conversations_list', {
            'conversations': conversations
        })
    
    @handle_request.register
    async def _(self, connection_id: str, request: GetContactsRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        contacts = await contact_service.get_user_contacts(str(user.id))
        
        await self._send_message(connection_id, 'contacts_list', {
            'contacts': contacts
        })
    
    @handle_request.register
    async def _(self, connection_id: str, request: SearchUsersRequest) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        users = await contact_service.search_users(request.query, str(user.id), request.limit)
        
        await self._send_message(connection_id, 'users_search_results', {
            'query': request.query,
            'users': users
        })
    
    def _get_user_id_from_connection(self, connection_id: str) -> Optional[str]:
        info = connection_manager.get_connection_info(connection_id)
        return info.get('user_id') if info else None
    
    async def _require_auth(self, connection_id: str) -> Optional[User]:
        info = connection_manager.get_connection_info(connection_id)
        if not info or not info.get('authenticated'):
            await self._send_error(connection_id, "AUTHENTICATION_REQUIRED", "Authentication required")
            return None
        
        try:
            user = await User.get(info['user_id'])
            return user
        except:
            await self._send_error(connection_id, "USER_NOT_FOUND", "User not found")
            return None
    
    async def _send_message(self, connection_id: str, message_type: str, data: Dict[str, Any]) -> None:
        message = {
            'type': message_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message_id': str(uuid.uuid4())
        }
        
        message_bytes = json.dumps(message).encode('utf-8')
        await connection_manager.send_to_connection(connection_id, message_bytes)
    
    async def _send_error(self, connection_id: str, code: str, message: str, details: Dict = None) -> None:
        await self._send_message(connection_id, 'error', {
            'code': code,
            'message': message,
            'details': details or {}
        })
    
    async def _broadcast_to_conversation(self, conversation_id: str, message_type: str, data: Dict[str, Any],
                                         exclude_user_id: str = None) -> None:
        message = {
            'type': message_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message_id': str(uuid.uuid4())
        }
        
        message_bytes = json.dumps(message).encode('utf-8')
        await connection_manager.send_to_conversation(conversation_id, message_bytes, exclude_user_id)


message_handler = DispatchMessageHandler()
