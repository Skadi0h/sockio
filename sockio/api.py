import json
from typing import Dict, Any, Optional
from socketify import App
from socketify.socketify import AppRequest, AppResponse

from sockio.auth import auth_manager, UserRegistrationRequest, UserLoginRequest
from sockio.chat_service import chat_service
from sockio.contact_service import contact_service
from sockio.file_service import file_service
from sockio.message_history_service import message_history_service
from sockio.models import User
from sockio.config import config
from sockio.log import make_logger

logger = make_logger("socketify_api")


class SocketifyAPI:
    def __init__(self, app: App):
        self.app = app
        self._setup_routes()
    
    def _setup_routes(self):
        self.app.post("/api/auth/register", self._handle_register)
        self.app.post("/api/auth/login", self._handle_login)
        self.app.post("/api/auth/logout", self._handle_logout)
        self.app.get("/api/users/me", self._handle_get_current_user)
        self.app.get("/api/users/:user_id", self._handle_get_user)
        self.app.get("/api/conversations", self._handle_get_conversations)
        self.app.post("/api/conversations/direct", self._handle_create_direct_chat)
        self.app.post("/api/conversations/group", self._handle_create_group)
        self.app.get("/api/conversations/:conversation_id/messages", self._handle_get_messages)
        self.app.get("/api/conversations/:conversation_id/participants", self._handle_get_participants)
        self.app.get("/api/contacts", self._handle_get_contacts)
        self.app.post("/api/contacts/request", self._handle_send_contact_request)
        self.app.post("/api/contacts/accept", self._handle_accept_contact_request)
        self.app.post("/api/contacts/decline", self._handle_decline_contact_request)
        self.app.delete("/api/contacts/:contact_user_id", self._handle_remove_contact)
        self.app.post("/api/contacts/block", self._handle_block_user)
        self.app.post("/api/contacts/unblock", self._handle_unblock_user)
        self.app.get("/api/contacts/pending", self._handle_get_pending_requests)
        self.app.get("/api/contacts/blocked", self._handle_get_blocked_users)
        self.app.get("/api/users/search", self._handle_search_users)
        self.app.post("/api/files/upload", self._handle_file_upload)
        self.app.get("/api/files/:file_id", self._handle_get_file)
        self.app.delete("/api/files/:file_id", self._handle_delete_file)
        self.app.get("/api/conversations/:conversation_id/history", self._handle_get_message_history)
        self.app.get("/api/conversations/:conversation_id/search", self._handle_search_messages)
        self.app.get("/api/conversations/:conversation_id/stats", self._handle_get_conversation_stats)
        self.app.get("/api/health", self._handle_health)
        self.app.get("/api/info", self._handle_info)
    
    def _set_cors_headers(self, res):
        res.write_header("Access-Control-Allow-Origin", "*")
        res.write_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        res.write_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
        res.write_header("Access-Control-Allow-Credentials", "true")
    
    def _send_json_response(self, res, data: Dict[str, Any], status: int = 200):
        self._set_cors_headers(res)
        res.write_header("Content-Type", "application/json")
        if status != 200:
            if status == 400:
                res.write_status("400 Bad Request")
            elif status == 401:
                res.write_status("401 Unauthorized")
            elif status == 404:
                res.write_status("404 Not Found")
            elif status == 500:
                res.write_status("500 Internal Server Error")
        res.end(json.dumps(data))
    
    def _send_error(self, res, message: str, status: int = 400, details: Dict = None):
        error_data = {
            "error": message,
            "status": status
        }
        if details:
            error_data["details"] = details
        self._send_json_response(res, error_data, status)
    
    def _get_session_token(self, req) -> Optional[str]:
        auth_header = req.get_header("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        return req.get_header("x-session-token")
    
    def _get_query_param(self, req, param: str, default: str = None) -> str:
        return req.get_query(param) or default
    
    async def _verify_session(self, req) -> Optional[User]:
        session_token = self._get_session_token(req)
        if not session_token:
            return None
        return await auth_manager.verify_session(session_token)
    
    async def _handle_register(self, res: AppResponse, req: AppRequest):
        try:
            body = await res.get_json()
            
            request = UserRegistrationRequest(**body)
            response = await auth_manager.register_user(request)
            
            if not response.success:
                self._send_error(res, response.message, 400)
                return
            
            self._send_json_response(res, response.dict())
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error in register", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_login(self, res: AppResponse, _: AppRequest):
        try:
            body = await res.get_json()
            request = UserLoginRequest(**body)
            response = await auth_manager.login_user(request)
            
            if not response.success:
                self._send_error(res, response.message, 401)
                return
            
            self._send_json_response(res, response.dict())
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error in login", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_logout(self, res, req):
        try:
            session_token = self._get_session_token(req)
            if not session_token:
                self._send_error(res, "Session token required", 401)
                return
            
            response = await auth_manager.logout_user(session_token)
            self._send_json_response(res, response.dict())
        
        except Exception as e:
            logger.error("Error in logout", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_current_user(self, res: AppResponse, req: AppRequest):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            self._send_json_response(res, user.to_dict())
        
        except Exception as e:
            logger.error("Error getting current user", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_user(self, res, req):
        try:
            user_id = req.get_parameter(0)
            if not user_id:
                self._send_error(res, "User ID required", 400)
                return
            
            user = await User.get(user_id)
            if not user:
                self._send_error(res, "User not found", 404)
                return
            
            self._send_json_response(res, user.to_dict())
        
        except Exception as e:
            logger.error("Error getting user", error=str(e))
            self._send_error(res, "User not found", 404)
    
    async def _handle_get_conversations(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            conversations = await chat_service.get_user_conversations(str(user.id))
            self._send_json_response(res, {"conversations": conversations})
        
        except Exception as e:
            logger.error("Error getting conversations", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_create_direct_chat(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "other_user_id" not in body:
                self._send_error(res, "other_user_id required", 400)
                return
            
            conversation = await chat_service.create_direct_conversation(str(user.id),
                                                                         body["other_user_id"])
            if not conversation:
                self._send_error(res, "Failed to create direct chat", 400)
                return
            
            self._send_json_response(res, conversation.to_dict())
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error creating direct chat", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_create_group(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "name" not in body:
                self._send_error(res, "Group name required", 400)
                return
            
            conversation = await chat_service.create_group_conversation(
                str(user.id),
                body["name"],
                body.get("description"),
                body.get("participant_ids", [])
            )
            
            if not conversation:
                self._send_error(res, "Failed to create group", 400)
                return
            
            self._send_json_response(res, conversation.to_dict())
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error creating group", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_messages(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            conversation_id = req.get_parameter(0)
            if not conversation_id:
                self._send_error(res, "Conversation ID required", 400)
                return
            
            limit = int(self._get_query_param(res, "limit", "50"))
            offset = int(self._get_query_param(res, "offset", "0"))
            
            messages = await chat_service.get_conversation_messages(conversation_id, limit, offset)
            
            messages_data = []
            for message in messages:
                message_dict = message.to_dict()
                if message.sender_id:
                    sender = await User.get(message.sender_id.id)
                    message_dict["sender"] = sender.to_dict() if sender else None
                messages_data.append(message_dict)
            
            self._send_json_response(res, {"messages": messages_data})
        
        except Exception as e:
            logger.error("Error getting messages", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_participants(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            conversation_id = req.get_parameter(0)
            if not conversation_id:
                self._send_error(res, "Conversation ID required", 400)
                return
            
            participants = await chat_service.get_conversation_participants(conversation_id)
            self._send_json_response(res, {"participants": participants})
        
        except Exception as e:
            logger.error("Error getting participants", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_contacts(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            contacts = await contact_service.get_user_contacts(str(user.id))
            self._send_json_response(res, {"contacts": contacts})
        
        except Exception as e:
            logger.error("Error getting contacts", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_send_contact_request(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "user_id" not in body:
                self._send_error(res, "user_id required", 400)
                return
            
            contact = await contact_service.send_contact_request(str(user.id), body["user_id"])
            if not contact:
                self._send_error(res, "Failed to send contact request", 400)
                return
            
            self._send_json_response(res, contact.to_dict())
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error sending contact request", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_accept_contact_request(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "contact_id" not in body:
                self._send_error(res, "contact_id required", 400)
                return
            
            success = await contact_service.accept_contact_request(str(user.id), body["contact_id"])
            if not success:
                self._send_error(res, "Failed to accept contact request", 400)
                return
            
            self._send_json_response(res, {"success": True})
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error accepting contact request", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_decline_contact_request(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "contact_id" not in body:
                self._send_error(res, "contact_id required", 400)
                return
            
            success = await contact_service.decline_contact_request(str(user.id), body["contact_id"])
            if not success:
                self._send_error(res, "Failed to decline contact request", 400)
                return
            
            self._send_json_response(res, {"success": True})
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error declining contact request", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_remove_contact(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            contact_user_id = req.get_parameter(0)
            if not contact_user_id:
                self._send_error(res, "contact_user_id required", 400)
                return
            
            success = await contact_service.remove_contact(str(user.id), contact_user_id)
            if not success:
                self._send_error(res, "Failed to remove contact", 400)
                return
            
            self._send_json_response(res, {"success": True})
        
        except Exception as e:
            logger.error("Error removing contact", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_block_user(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "user_id" not in body:
                self._send_error(res, "user_id required", 400)
                return
            
            success = await contact_service.block_user(str(user.id), body["user_id"])
            if not success:
                self._send_error(res, "Failed to block user", 400)
                return
            
            self._send_json_response(res, {"success": True})
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error blocking user", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_unblock_user(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body_str = res.get_data().decode("utf-8")
            body = json.loads(body_str)
            
            if "user_id" not in body:
                self._send_error(res, "user_id required", 400)
                return
            
            success = await contact_service.unblock_user(str(user.id), body["user_id"])
            if not success:
                self._send_error(res, "Failed to unblock user", 400)
                return
            
            self._send_json_response(res, {"success": True})
        
        except json.JSONDecodeError:
            self._send_error(res, "Invalid JSON body", 400)
        except Exception as e:
            logger.error("Error unblocking user", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_pending_requests(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            pending_requests = await contact_service.get_pending_requests(str(user.id))
            self._send_json_response(res, pending_requests)
        
        except Exception as e:
            logger.error("Error getting pending requests", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_blocked_users(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            blocked_users = await contact_service.get_blocked_users(str(user.id))
            self._send_json_response(res, {"blocked_users": blocked_users})
        
        except Exception as e:
            logger.error("Error getting blocked users", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_search_users(self, res: AppResponse, req: AppRequest):
        logger.info('In search users [0]')
        req.preserve()
        try:
            user = await self._verify_session(req)
            logger.info('In search users [1]')
            if not user:
                logger.info('In search users [2]')
               
                self._send_error(res, "Invalid session", 401)
                return
            logger.info('In search users [3]')
            query = req.get_query('q')
            logger.info('In search users [4]', query=query)
            if not query:
                logger.info('In search users [5]')
                self._send_error(res, "Search query required", 400)
                return
            
            #limit = int(self._get_query_param(req, "limit", "20"))
            logger.info('In search users [6]')
            users = await contact_service.search_users(query[1], str(user.id), 20)
            logger.info('In search users [7]')
            
            self._send_json_response(res, {"users": users})
            logger.info('In search users [8]')
        
        except Exception as e:
            logger.info('In search users [9]')
            logger.error("Error searching users", error=str(e))
            self._send_error(res, "Internal server error", 500)
        logger.info('In search users [10]')
    
    async def _handle_health(self, res, req):
        self._send_json_response(res, {"status": "healthy"})
    
    async def _handle_info(self, res, req):
        self._send_json_response(res, {
            "name": "Chat API",
            "version": "1.0.0",
            "websocket_url": config.ws_url
        })
    
    async def _handle_file_upload(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            body = await self._get_request_body(res, req)
            if not body:
                self._send_error(res, "No file data provided", 400)
                return
            
            content_type = req.get_header("content-type") or ""
            if not content_type.startswith("multipart/form-data"):
                self._send_error(res, "Multipart form data required", 400)
                return
            
            filename = req.get_header("x-filename") or "unknown"
            mime_type = req.get_header("x-mime-type") or "application/octet-stream"
            
            attachment = await file_service.save_file(body, filename, mime_type, str(user.id))
            if not attachment:
                self._send_error(res, "Failed to save file", 500)
                return
            
            self._send_json_response(res, {
                "file_id": str(attachment.id),
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "mime_type": attachment.mime_type
            }, 201)
        
        except Exception as e:
            logger.error("Error uploading file", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_file(self, res, req):
        try:
            file_id = req.get_parameter(0)
            if not file_id:
                self._send_error(res, "File ID required", 400)
                return
            
            attachment = await file_service.get_file(file_id)
            if not attachment:
                self._send_error(res, "File not found", 404)
                return
            
            file_data = await file_service.get_file_data(attachment.file_path)
            if not file_data:
                self._send_error(res, "File data not found", 404)
                return
            
            res.write_header("Content-Type", attachment.mime_type)
            res.write_header("Content-Length", str(len(file_data)))
            res.write_header("Content-Disposition", f'attachment; filename="{attachment.filename}"')
            self._set_cors_headers(res)
            res.end(file_data)
        
        except Exception as e:
            logger.error("Error getting file", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_delete_file(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            file_id = req.get_parameter(0)
            if not file_id:
                self._send_error(res, "File ID required", 400)
                return
            
            success = await file_service.delete_file(file_id, str(user.id))
            if not success:
                self._send_error(res, "Failed to delete file", 400)
                return
            
            self._send_json_response(res, {"message": "File deleted successfully"})
        
        except Exception as e:
            logger.error("Error deleting file", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_message_history(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            conversation_id = req.get_parameter(0)
            if not conversation_id:
                self._send_error(res, "Conversation ID required", 400)
                return
            
            limit = int(self._get_query_param(req, "limit", "50"))
            before = self._get_query_param(req, "before")
            
            messages = await message_history_service.get_conversation_messages(
                conversation_id, str(user.id), limit, before
            )
            
            self._send_json_response(res, {"messages": messages})
        
        except Exception as e:
            logger.error("Error getting message history", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_search_messages(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            conversation_id = req.get_parameter(0)
            if not conversation_id:
                self._send_error(res, "Conversation ID required", 400)
                return
            
            query = self._get_query_param(req, "q")
            if not query:
                self._send_error(res, "Search query required", 400)
                return
            
            limit = int(self._get_query_param(req, "limit", "20"))
            
            messages = await message_history_service.search_messages(
                conversation_id, str(user.id), query, limit
            )
            
            self._send_json_response(res, {"messages": messages})
        
        except Exception as e:
            logger.error("Error searching messages", error=str(e))
            self._send_error(res, "Internal server error", 500)
    
    async def _handle_get_conversation_stats(self, res, req):
        try:
            user = await self._verify_session(req)
            if not user:
                self._send_error(res, "Invalid session", 401)
                return
            
            conversation_id = req.get_parameter(0)
            if not conversation_id:
                self._send_error(res, "Conversation ID required", 400)
                return
            
            stats = await message_history_service.get_conversation_stats(
                conversation_id, str(user.id)
            )
            
            if not stats:
                self._send_error(res, "Conversation not found or access denied", 404)
                return
            
            self._send_json_response(res, stats)
        
        except Exception as e:
            logger.error("Error getting conversation stats", error=str(e))
            self._send_error(res, "Internal server error", 500)
