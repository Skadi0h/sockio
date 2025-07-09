import json
from typing import Dict, Any, Optional
from sockio.models import User
from sockio.connection_manager import connection_manager
from sockio.contact_service import contact_service
from sockio.log import make_logger

logger = make_logger("sockio.contact_handlers")


class ContactHandlers:
    def __init__(self):
        pass
    
    async def _send_message(self, connection_id: str, message_type: str, data: Dict[str, Any]) -> None:
        from datetime import datetime, timezone
        import uuid
        
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
    
    async def handle_send_contact_request(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        target_user_id = data.get('user_id')
        if not target_user_id:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "user_id is required")
            return
        
        contact = await contact_service.send_contact_request(str(user.id), target_user_id)
        
        if contact:
            target_user = await User.get(target_user_id)
            
            await self._send_message(connection_id, 'contact_request_sent', {
                'contact': contact.to_dict(),
                'target_user': target_user.to_dict() if target_user else None
            })
            
            await connection_manager.send_to_user(target_user_id, json.dumps({
                'type': 'contact_request_received',
                'data': {
                    'contact': contact.to_dict(),
                    'from_user': user.to_dict()
                }
            }).encode('utf-8'))
        else:
            await self._send_error(connection_id, "CONTACT_REQUEST_FAILED", "Failed to send contact request")
    
    async def handle_accept_contact_request(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        contact_id = data.get('contact_id')
        if not contact_id:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "contact_id is required")
            return
        
        success = await contact_service.accept_contact_request(str(user.id), contact_id)
        
        if success:
            from sockio.models import Contact
            contact = await Contact.get(contact_id)
            from_user = await User.get(contact.user_id.id)
            
            await self._send_message(connection_id, 'contact_request_accepted', {
                'contact_id': contact_id,
                'contact_user': from_user.to_dict() if from_user else None
            })
            
            await connection_manager.send_to_user(str(contact.user_id.id), json.dumps({
                'type': 'contact_request_accepted',
                'data': {
                    'contact_id': contact_id,
                    'accepted_by': user.to_dict()
                }
            }).encode('utf-8'))
        else:
            await self._send_error(connection_id, "CONTACT_REQUEST_FAILED", "Failed to accept contact request")
    
    async def handle_decline_contact_request(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        contact_id = data.get('contact_id')
        if not contact_id:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "contact_id is required")
            return
        
        success = await contact_service.decline_contact_request(str(user.id), contact_id)
        
        if success:
            await self._send_message(connection_id, 'contact_request_declined', {
                'contact_id': contact_id
            })
        else:
            await self._send_error(connection_id, "CONTACT_REQUEST_FAILED", "Failed to decline contact request")
    
    async def handle_remove_contact(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        contact_user_id = data.get('contact_user_id')
        if not contact_user_id:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "contact_user_id is required")
            return
        
        success = await contact_service.remove_contact(str(user.id), contact_user_id)
        
        if success:
            await self._send_message(connection_id, 'contact_removed', {
                'contact_user_id': contact_user_id
            })
            
            await connection_manager.send_to_user(contact_user_id, json.dumps({
                'type': 'contact_removed',
                'data': {
                    'removed_by_user_id': str(user.id)
                }
            }).encode('utf-8'))
        else:
            await self._send_error(connection_id, "CONTACT_REMOVAL_FAILED", "Failed to remove contact")
    
    async def handle_block_user(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        blocked_user_id = data.get('user_id')
        if not blocked_user_id:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "user_id is required")
            return
        
        success = await contact_service.block_user(str(user.id), blocked_user_id)
        
        if success:
            blocked_user = await User.get(blocked_user_id)
            await self._send_message(connection_id, 'user_blocked', {
                'blocked_user': blocked_user.to_dict() if blocked_user else None
            })
        else:
            await self._send_error(connection_id, "BLOCK_FAILED", "Failed to block user")
    
    async def handle_unblock_user(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        blocked_user_id = data.get('user_id')
        if not blocked_user_id:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "user_id is required")
            return
        
        success = await contact_service.unblock_user(str(user.id), blocked_user_id)
        
        if success:
            await self._send_message(connection_id, 'user_unblocked', {
                'unblocked_user_id': blocked_user_id
            })
        else:
            await self._send_error(connection_id, "UNBLOCK_FAILED", "Failed to unblock user")
    
    async def handle_get_contacts(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        contacts = await contact_service.get_user_contacts(str(user.id))
        
        await self._send_message(connection_id, 'contacts_list', {
            'contacts': contacts
        })
    
    async def handle_get_pending_requests(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        requests = await contact_service.get_pending_requests(str(user.id))
        
        await self._send_message(connection_id, 'pending_requests', requests)
    
    async def handle_get_blocked_users(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        blocked_users = await contact_service.get_blocked_users(str(user.id))
        
        await self._send_message(connection_id, 'blocked_users_list', {
            'blocked_users': blocked_users
        })
    
    async def handle_search_users(self, connection_id: str, data: Dict[str, Any]) -> None:
        user = await self._require_auth(connection_id)
        if not user:
            return
        
        query = data.get('query')
        limit = data.get('limit', 20)
        
        if not query:
            await self._send_error(connection_id, "INVALID_MESSAGE_FORMAT", "query is required")
            return
        
        users = await contact_service.search_users(query, str(user.id), limit)
        
        await self._send_message(connection_id, 'users_search_results', {
            'query': query,
            'users': users
        })


contact_handlers = ContactHandlers()

