from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sockio.models import User, Contact, ContactStatus
from sockio.log import make_logger, ChatLogger

logger = make_logger("sockio.contact_service")
chat_logger = ChatLogger()


class ContactService:
    def __init__(self):
        pass
    
    async def send_contact_request(self, from_user_id: str, to_user_id: str) -> Optional[Contact]:
        try:
            if from_user_id == to_user_id:
                return None
            
            from_user = await User.get(from_user_id)
            to_user = await User.get(to_user_id)
            
            if not from_user or not to_user:
                return None
            
            existing_contact = await Contact.find_one(
                Contact.user_id.id == from_user_id,
                Contact.contact_user_id.id == to_user_id
            )
            
            if existing_contact:
                return None
            
            reverse_contact = await Contact.find_one(
                Contact.user_id.id == to_user_id,
                Contact.contact_user_id.id == from_user_id
            )
            
            if reverse_contact:
                return None
            
            contact = Contact(
                user_id=from_user,
                contact_user_id=to_user,
                status=ContactStatus.PENDING
            )
            
            await contact.insert()
            
            chat_logger.contact_request_sent(from_user_id, to_user_id)
            
            return contact
            
        except Exception as e:
            logger.error("Error sending contact request", error=str(e))
            return None
    
    async def accept_contact_request(self, user_id: str, contact_id: str) -> bool:
        try:
            contact = await Contact.get(contact_id)
            
            if not contact or str(contact.contact_user_id.id) != user_id:
                return False
            
            if contact.status != ContactStatus.PENDING:
                return False
            
            contact.status = ContactStatus.ACCEPTED
            contact.updated_at = datetime.now(timezone.utc)
            await contact.save()
            
            reverse_contact = Contact(
                user_id=contact.contact_user_id,
                contact_user_id=contact.user_id,
                status=ContactStatus.ACCEPTED
            )
            await reverse_contact.insert()
            
            chat_logger.contact_request_accepted(str(contact.user_id.id), user_id)
            
            return True
            
        except Exception as e:
            logger.error("Error accepting contact request", error=str(e))
            return False
    
    async def decline_contact_request(self, user_id: str, contact_id: str) -> bool:
        try:
            contact = await Contact.get(contact_id)
            
            if not contact or str(contact.contact_user_id.id) != user_id:
                return False
            
            if contact.status != ContactStatus.PENDING:
                return False
            
            contact.status = ContactStatus.DECLINED
            contact.updated_at = datetime.now(timezone.utc)
            await contact.save()
            
            return True
            
        except Exception as e:
            logger.error("Error declining contact request", error=str(e))
            return False
    
    async def remove_contact(self, user_id: str, contact_user_id: str) -> bool:
        try:
            contact = await Contact.find_one(
                Contact.user_id.id == user_id,
                Contact.contact_user_id.id == contact_user_id,
                Contact.status == ContactStatus.ACCEPTED
            )
            
            reverse_contact = await Contact.find_one(
                Contact.user_id.id == contact_user_id,
                Contact.contact_user_id.id == user_id,
                Contact.status == ContactStatus.ACCEPTED
            )
            
            if contact:
                await contact.delete()
            
            if reverse_contact:
                await reverse_contact.delete()
            
            return True
            
        except Exception as e:
            logger.error("Error removing contact", error=str(e))
            return False
    
    async def block_user(self, user_id: str, blocked_user_id: str) -> bool:
        try:
            if user_id == blocked_user_id:
                return False
            
            user = await User.get(user_id)
            blocked_user = await User.get(blocked_user_id)
            
            if not user or not blocked_user:
                return False
            
            existing_contact = await Contact.find_one(
                Contact.user_id.id == user_id,
                Contact.contact_user_id.id == blocked_user_id
            )
            
            if existing_contact:
                existing_contact.status = ContactStatus.BLOCKED
                existing_contact.updated_at = datetime.now(timezone.utc)
                await existing_contact.save()
            else:
                contact = Contact(
                    user_id=user,
                    contact_user_id=blocked_user,
                    status=ContactStatus.BLOCKED
                )
                await contact.insert()
            
            reverse_contact = await Contact.find_one(
                Contact.user_id.id == blocked_user_id,
                Contact.contact_user_id.id == user_id
            )
            
            if reverse_contact:
                await reverse_contact.delete()
            
            return True
            
        except Exception as e:
            logger.error("Error blocking user", error=str(e))
            return False
    
    async def unblock_user(self, user_id: str, blocked_user_id: str) -> bool:
        try:
            contact = await Contact.find_one(
                Contact.user_id.id == user_id,
                Contact.contact_user_id.id == blocked_user_id,
                Contact.status == ContactStatus.BLOCKED
            )
            
            if contact:
                await contact.delete()
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error unblocking user", error=str(e))
            return False
    
    async def get_user_contacts(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            contacts = await Contact.find(
                Contact.user_id.id == user_id,
                Contact.status == ContactStatus.ACCEPTED
            ).to_list()
            
            result = []
            for contact in contacts:
                contact_user = await User.get(contact.contact_user_id.id)
                if contact_user:
                    contact_data = contact.to_dict()
                    contact_data['contact_user'] = contact_user.to_dict()
                    result.append(contact_data)
            
            return result
            
        except Exception as e:
            logger.error("Error getting user contacts", error=str(e))
            return []
    
    async def get_pending_requests(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            incoming_requests = await Contact.find(
                Contact.contact_user_id.id == user_id,
                Contact.status == ContactStatus.PENDING
            ).to_list()
            
            outgoing_requests = await Contact.find(
                Contact.user_id.id == user_id,
                Contact.status == ContactStatus.PENDING
            ).to_list()
            
            result = {
                'incoming': [],
                'outgoing': []
            }
            
            for request in incoming_requests:
                from_user = await User.get(request.user_id.id)
                if from_user:
                    request_data = request.to_dict()
                    request_data['from_user'] = from_user.to_dict()
                    result['incoming'].append(request_data)
            
            for request in outgoing_requests:
                to_user = await User.get(request.contact_user_id.id)
                if to_user:
                    request_data = request.to_dict()
                    request_data['to_user'] = to_user.to_dict()
                    result['outgoing'].append(request_data)
            
            return result
            
        except Exception as e:
            logger.error("Error getting pending requests", error=str(e))
            return {'incoming': [], 'outgoing': []}
    
    async def get_blocked_users(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            blocked_contacts = await Contact.find(
                Contact.user_id.id == user_id,
                Contact.status == ContactStatus.BLOCKED
            ).to_list()
            
            result = []
            for contact in blocked_contacts:
                blocked_user = await User.get(contact.contact_user_id.id)
                if blocked_user:
                    contact_data = contact.to_dict()
                    contact_data['blocked_user'] = blocked_user.to_dict()
                    result.append(contact_data)
            
            return result
            
        except Exception as e:
            logger.error("Error getting blocked users", error=str(e))
            return []
    
    async def search_users(self, query: str, current_user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            users = await User.find(
                {"$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"display_name": {"$regex": query, "$options": "i"}}
                ]}
            ).limit(limit).to_list()
            
            result = []
            for user in users:
                if str(user.id) == current_user_id:
                    continue
                
                user_data = user.to_dict()
                
                contact = await Contact.find_one(
                    Contact.user_id.id == current_user_id,
                    Contact.contact_user_id.id == str(user.id)
                )
                
                if contact:
                    user_data['contact_status'] = contact.status
                else:
                    user_data['contact_status'] = None
                
                result.append(user_data)
            
            return result
            
        except Exception as e:
            logger.error("Error searching users", error=str(e))
            return []
    
    async def is_contact(self, user_id: str, other_user_id: str) -> bool:
        try:
            contact = await Contact.find_one(
                Contact.user_id.id == user_id,
                Contact.contact_user_id.id == other_user_id,
                Contact.status == ContactStatus.ACCEPTED
            )
            
            return contact is not None
            
        except Exception as e:
            logger.error("Error checking contact status", error=str(e))
            return False
    
    async def is_blocked(self, user_id: str, other_user_id: str) -> bool:
        try:
            blocked_contact = await Contact.find_one(
                Contact.user_id.id == other_user_id,
                Contact.contact_user_id.id == user_id,
                Contact.status == ContactStatus.BLOCKED
            )
            
            return blocked_contact is not None
            
        except Exception as e:
            logger.error("Error checking blocked status", error=str(e))
            return False


contact_service = ContactService()

