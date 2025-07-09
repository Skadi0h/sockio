import json
from typing import Dict, Any
from sockio.config import config


def generate_openapi_spec() -> Dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "WebSocket Chat Server API",
            "description": "A comprehensive chat API with WebSocket support, user management, conversations, and file attachments",
            "version": "1.0.0",
            "contact": {
                "name": "Chat API Support",
                "email": "support@chatapi.com"
            }
        },
        "servers": [
            {
                "url": config.http_url,
                "description": "Development server"
            }
        ],
        "components": {
            "securitySchemes": {
                "SessionToken": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Session-Token",
                    "description": "Session token obtained from login"
                }
            },
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "User ID"},
                        "username": {"type": "string", "description": "Username"},
                        "email": {"type": "string", "format": "email", "description": "Email address"},
                        "display_name": {"type": "string", "description": "Display name"},
                        "status": {"type": "string", "enum": ["online", "offline", "away", "busy"], "description": "User status"},
                        "avatar_url": {"type": "string", "description": "Avatar URL"},
                        "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                        "last_seen": {"type": "string", "format": "date-time", "description": "Last seen timestamp"}
                    }
                },
                "Conversation": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Conversation ID"},
                        "type": {"type": "string", "enum": ["direct", "group"], "description": "Conversation type"},
                        "name": {"type": "string", "description": "Conversation name (for groups)"},
                        "description": {"type": "string", "description": "Conversation description"},
                        "avatar_url": {"type": "string", "description": "Conversation avatar URL"},
                        "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                        "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
                        "last_message": {"$ref": "#/components/schemas/Message"},
                        "participants": {"type": "array", "items": {"$ref": "#/components/schemas/ConversationParticipant"}}
                    }
                },
                "Message": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Message ID"},
                        "conversation_id": {"type": "string", "description": "Conversation ID"},
                        "sender_id": {"type": "string", "description": "Sender user ID"},
                        "content": {"type": "string", "description": "Message content"},
                        "message_type": {"type": "string", "enum": ["text", "image", "video", "audio", "file"], "description": "Message type"},
                        "attachments": {"type": "array", "items": {"$ref": "#/components/schemas/FileAttachment"}},
                        "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                        "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
                        "edited_at": {"type": "string", "format": "date-time", "description": "Edit timestamp"},
                        "is_deleted": {"type": "boolean", "description": "Whether message is deleted"}
                    }
                },
                "FileAttachment": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Attachment ID"},
                        "filename": {"type": "string", "description": "Original filename"},
                        "file_path": {"type": "string", "description": "File path on server"},
                        "file_size": {"type": "integer", "description": "File size in bytes"},
                        "mime_type": {"type": "string", "description": "MIME type"},
                        "uploaded_at": {"type": "string", "format": "date-time", "description": "Upload timestamp"}
                    }
                },
                "ConversationParticipant": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"},
                        "role": {"type": "string", "enum": ["admin", "member"], "description": "Participant role"},
                        "joined_at": {"type": "string", "format": "date-time", "description": "Join timestamp"},
                        "left_at": {"type": "string", "format": "date-time", "description": "Leave timestamp"}
                    }
                },
                "Contact": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Contact ID"},
                        "user_id": {"type": "string", "description": "User ID"},
                        "contact_user_id": {"type": "string", "description": "Contact user ID"},
                        "status": {"type": "string", "enum": ["pending", "accepted", "declined", "blocked"], "description": "Contact status"},
                        "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                        "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"}
                    }
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string", "description": "Username or email"},
                        "password": {"type": "string", "description": "Password"}
                    }
                },
                "RegisterRequest": {
                    "type": "object",
                    "required": ["username", "email", "password"],
                    "properties": {
                        "username": {"type": "string", "description": "Username"},
                        "email": {"type": "string", "format": "email", "description": "Email address"},
                        "password": {"type": "string", "description": "Password"},
                        "display_name": {"type": "string", "description": "Display name"}
                    }
                },
                "CreateConversationRequest": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["direct", "group"], "description": "Conversation type"},
                        "participant_ids": {"type": "array", "items": {"type": "string"}, "description": "Participant user IDs"},
                        "name": {"type": "string", "description": "Group name (required for groups)"},
                        "description": {"type": "string", "description": "Group description"}
                    }
                },
                "ContactRequest": {
                    "type": "object",
                    "required": ["contact_user_id"],
                    "properties": {
                        "contact_user_id": {"type": "string", "description": "User ID to add as contact"}
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string", "description": "Error message"},
                        "code": {"type": "string", "description": "Error code"}
                    }
                },
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Success message"},
                        "data": {"type": "object", "description": "Response data"}
                    }
                }
            }
        },
        "security": [
            {"SessionToken": []}
        ],
        "paths": {
            "/api/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Register a new user",
                    "description": "Create a new user account",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RegisterRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User registered successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Login user",
                    "description": "Authenticate user and create session",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "session_token": {"type": "string", "description": "Session token"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/logout": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Logout user",
                    "description": "Invalidate user session",
                    "responses": {
                        "200": {
                            "description": "Logout successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/users/me": {
                "get": {
                    "tags": ["Users"],
                    "summary": "Get current user",
                    "description": "Get current authenticated user information",
                    "responses": {
                        "200": {
                            "description": "User information",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/users/search": {
                "get": {
                    "tags": ["Users"],
                    "summary": "Search users",
                    "description": "Search for users by username or email",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Search query"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/conversations": {
                "get": {
                    "tags": ["Conversations"],
                    "summary": "Get user conversations",
                    "description": "Get all conversations for the authenticated user",
                    "responses": {
                        "200": {
                            "description": "List of conversations",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Conversation"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["Conversations"],
                    "summary": "Create conversation",
                    "description": "Create a new conversation (direct or group)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateConversationRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Conversation created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Conversation"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/conversations/{conversation_id}/messages": {
                "get": {
                    "tags": ["Messages"],
                    "summary": "Get conversation messages",
                    "description": "Get messages for a specific conversation",
                    "parameters": [
                        {
                            "name": "conversation_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Conversation ID"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 50},
                            "description": "Number of messages to retrieve"
                        },
                        {
                            "name": "before",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Get messages before this message ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of messages",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Message"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/conversations/{conversation_id}/participants": {
                "get": {
                    "tags": ["Conversations"],
                    "summary": "Get conversation participants",
                    "description": "Get participants of a conversation",
                    "parameters": [
                        {
                            "name": "conversation_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Conversation ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of participants",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/ConversationParticipant"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts": {
                "get": {
                    "tags": ["Contacts"],
                    "summary": "Get user contacts",
                    "description": "Get all contacts for the authenticated user",
                    "responses": {
                        "200": {
                            "description": "List of contacts",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Contact"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/request": {
                "post": {
                    "tags": ["Contacts"],
                    "summary": "Send contact request",
                    "description": "Send a contact request to another user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ContactRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Contact request sent",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/accept": {
                "post": {
                    "tags": ["Contacts"],
                    "summary": "Accept contact request",
                    "description": "Accept a pending contact request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ContactRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Contact request accepted",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/decline": {
                "post": {
                    "tags": ["Contacts"],
                    "summary": "Decline contact request",
                    "description": "Decline a pending contact request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ContactRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Contact request declined",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/{contact_user_id}": {
                "delete": {
                    "tags": ["Contacts"],
                    "summary": "Remove contact",
                    "description": "Remove a contact from user's contact list",
                    "parameters": [
                        {
                            "name": "contact_user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Contact user ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Contact removed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/block": {
                "post": {
                    "tags": ["Contacts"],
                    "summary": "Block user",
                    "description": "Block a user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ContactRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User blocked",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/unblock": {
                "post": {
                    "tags": ["Contacts"],
                    "summary": "Unblock user",
                    "description": "Unblock a previously blocked user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ContactRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User unblocked",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/pending": {
                "get": {
                    "tags": ["Contacts"],
                    "summary": "Get pending contact requests",
                    "description": "Get all pending contact requests (incoming and outgoing)",
                    "responses": {
                        "200": {
                            "description": "List of pending requests",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "incoming": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Contact"}
                                            },
                                            "outgoing": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Contact"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/contacts/blocked": {
                "get": {
                    "tags": ["Contacts"],
                    "summary": "Get blocked users",
                    "description": "Get all blocked users",
                    "responses": {
                        "200": {
                            "description": "List of blocked users",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Contact"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Health check",
                    "description": "Check if the server is running",
                    "security": [],
                    "responses": {
                        "200": {
                            "description": "Server is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/info": {
                "get": {
                    "tags": ["System"],
                    "summary": "Server information",
                    "description": "Get server information and statistics",
                    "security": [],
                    "responses": {
                        "200": {
                            "description": "Server information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "version": {"type": "string"},
                                            "websocket_url": {"type": "string"},
                                            "connections": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "Authentication",
                "description": "User authentication and session management"
            },
            {
                "name": "Users",
                "description": "User management and search"
            },
            {
                "name": "Conversations",
                "description": "Conversation management"
            },
            {
                "name": "Messages",
                "description": "Message management and history"
            },
            {
                "name": "Contacts",
                "description": "Contact and friend management"
            },
            {
                "name": "System",
                "description": "System health and information"
            }
        ]
    }


def get_openapi_json() -> str:
    return json.dumps(generate_openapi_spec(), indent=2)

