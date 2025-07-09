def get_websocket_docs() -> dict:
    return {
        "websocket_protocol": {
            "description": "WebSocket Chat Protocol Documentation",
            "connection": {
                "url": "/ws",
                "description": "WebSocket endpoint for real-time communication"
            },
            "authentication": {
                "description": "Authentication is required for most WebSocket operations",
                "method": "Send an 'authenticate' message with session token",
                "example": {
                    "type": "authenticate",
                    "data": {
                        "session_token": "your-session-token-here"
                    }
                }
            },
            "message_types": {
                "authenticate": {
                    "description": "Authenticate the WebSocket connection",
                    "direction": "client -> server",
                    "data": {
                        "session_token": "string - Session token from login"
                    },
                    "response": {
                        "type": "auth_success",
                        "data": {
                            "user_id": "string",
                            "username": "string"
                        }
                    }
                },
                "send_message": {
                    "description": "Send a message to a conversation",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Target conversation ID",
                        "content": "string - Message content",
                        "message_type": "string - text|image|video|audio|file",
                        "attachments": "array - Optional file attachments"
                    },
                    "response": {
                        "type": "message_sent",
                        "data": {
                            "message_id": "string",
                            "conversation_id": "string",
                            "timestamp": "string"
                        }
                    }
                },
                "edit_message": {
                    "description": "Edit an existing message",
                    "direction": "client -> server",
                    "data": {
                        "message_id": "string - Message ID to edit",
                        "content": "string - New message content"
                    },
                    "response": {
                        "type": "message_edited",
                        "data": {
                            "message_id": "string",
                            "updated_at": "string"
                        }
                    }
                },
                "delete_message": {
                    "description": "Delete a message",
                    "direction": "client -> server",
                    "data": {
                        "message_id": "string - Message ID to delete"
                    },
                    "response": {
                        "type": "message_deleted",
                        "data": {
                            "message_id": "string"
                        }
                    }
                },
                "typing_start": {
                    "description": "Indicate user started typing",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Conversation ID"
                    }
                },
                "typing_stop": {
                    "description": "Indicate user stopped typing",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Conversation ID"
                    }
                },
                "join_conversation": {
                    "description": "Join a conversation to receive messages",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Conversation ID to join"
                    },
                    "response": {
                        "type": "conversation_joined",
                        "data": {
                            "conversation_id": "string"
                        }
                    }
                },
                "leave_conversation": {
                    "description": "Leave a conversation",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Conversation ID to leave"
                    },
                    "response": {
                        "type": "conversation_left",
                        "data": {
                            "conversation_id": "string"
                        }
                    }
                },
                "create_group": {
                    "description": "Create a new group conversation",
                    "direction": "client -> server",
                    "data": {
                        "name": "string - Group name",
                        "description": "string - Optional group description",
                        "participant_ids": "array - Array of user IDs to add"
                    },
                    "response": {
                        "type": "group_created",
                        "data": {
                            "conversation_id": "string",
                            "name": "string"
                        }
                    }
                },
                "create_direct_chat": {
                    "description": "Create a direct conversation with another user",
                    "direction": "client -> server",
                    "data": {
                        "participant_id": "string - Other user's ID"
                    },
                    "response": {
                        "type": "direct_chat_created",
                        "data": {
                            "conversation_id": "string",
                            "participant_id": "string"
                        }
                    }
                },
                "get_message_history": {
                    "description": "Get message history for a conversation",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Conversation ID",
                        "limit": "number - Optional, default 50",
                        "before": "string - Optional message ID for pagination"
                    },
                    "response": {
                        "type": "message_history",
                        "data": {
                            "conversation_id": "string",
                            "messages": "array - Array of message objects"
                        }
                    }
                },
                "get_participants": {
                    "description": "Get participants of a conversation",
                    "direction": "client -> server",
                    "data": {
                        "conversation_id": "string - Conversation ID"
                    },
                    "response": {
                        "type": "participants_list",
                        "data": {
                            "conversation_id": "string",
                            "participants": "array - Array of participant objects"
                        }
                    }
                }
            },
            "server_events": {
                "new_message": {
                    "description": "Broadcast when a new message is received",
                    "direction": "server -> client",
                    "data": {
                        "message_id": "string",
                        "conversation_id": "string",
                        "sender_id": "string",
                        "content": "string",
                        "message_type": "string",
                        "created_at": "string",
                        "attachments": "array"
                    }
                },
                "message_edited": {
                    "description": "Broadcast when a message is edited",
                    "direction": "server -> client",
                    "data": {
                        "message_id": "string",
                        "conversation_id": "string",
                        "content": "string",
                        "edited_at": "string"
                    }
                },
                "message_deleted": {
                    "description": "Broadcast when a message is deleted",
                    "direction": "server -> client",
                    "data": {
                        "message_id": "string",
                        "conversation_id": "string"
                    }
                },
                "user_typing": {
                    "description": "Broadcast when a user starts typing",
                    "direction": "server -> client",
                    "data": {
                        "user_id": "string",
                        "conversation_id": "string",
                        "username": "string"
                    }
                },
                "user_stopped_typing": {
                    "description": "Broadcast when a user stops typing",
                    "direction": "server -> client",
                    "data": {
                        "user_id": "string",
                        "conversation_id": "string"
                    }
                },
                "user_joined": {
                    "description": "Broadcast when a user joins a conversation",
                    "direction": "server -> client",
                    "data": {
                        "user_id": "string",
                        "conversation_id": "string",
                        "username": "string"
                    }
                },
                "user_left": {
                    "description": "Broadcast when a user leaves a conversation",
                    "direction": "server -> client",
                    "data": {
                        "user_id": "string",
                        "conversation_id": "string"
                    }
                },
                "contact_request": {
                    "description": "Notify when receiving a contact request",
                    "direction": "server -> client",
                    "data": {
                        "from_user_id": "string",
                        "from_username": "string",
                        "request_id": "string"
                    }
                },
                "contact_accepted": {
                    "description": "Notify when contact request is accepted",
                    "direction": "server -> client",
                    "data": {
                        "user_id": "string",
                        "username": "string"
                    }
                },
                "error": {
                    "description": "Error response for failed operations",
                    "direction": "server -> client",
                    "data": {
                        "error": "string - Error message",
                        "code": "string - Error code",
                        "request_id": "string - Optional request ID"
                    }
                }
            },
            "error_codes": {
                "AUTH_REQUIRED": "Authentication required for this operation",
                "INVALID_TOKEN": "Invalid or expired session token",
                "CONVERSATION_NOT_FOUND": "Conversation not found or access denied",
                "MESSAGE_NOT_FOUND": "Message not found or access denied",
                "USER_NOT_FOUND": "User not found",
                "PERMISSION_DENIED": "Insufficient permissions for this operation",
                "RATE_LIMITED": "Too many requests, please slow down",
                "INVALID_DATA": "Invalid request data format",
                "SERVER_ERROR": "Internal server error"
            },
            "connection_states": {
                "connecting": "Initial connection state",
                "authenticating": "Waiting for authentication",
                "authenticated": "Successfully authenticated",
                "disconnected": "Connection closed"
            }
        }
    }

