from typing import Any

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from sockio.auth import (
    UserLoginRequest,
    UserRegistrationRequest,
    auth_manager,
)
from sockio.chat_service import chat_service
from sockio.config import config
from sockio.contact_service import contact_service
from sockio.file_service import file_service
from sockio.message_history_service import message_history_service
from sockio.models import User


class DirectChatRequest(BaseModel):
    other_user_id: str


class GroupChatRequest(BaseModel):
    name: str
    description: str | None = None
    participant_ids: list[str] = []


class ContactIdRequest(BaseModel):
    contact_id: str


class UserIdRequest(BaseModel):
    user_id: str


app = FastAPI(title="SockIO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def _extract_token(
    authorization: str | None = Header(None),
    session_token: str | None = Header(None, alias="X-Session-Token"),
) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    if session_token:
        return session_token
    raise HTTPException(status_code=401, detail="Session token required")


async def get_current_user(token: str = Depends(_extract_token)) -> User:
    user = await auth_manager.verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


@app.post("/api/auth/register")
async def register(data: UserRegistrationRequest):
    response = await auth_manager.register_user(data)
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response.dict()


@app.post("/api/auth/login")
async def login(data: UserLoginRequest):
    response = await auth_manager.login_user(data)
    if not response.success:
        raise HTTPException(status_code=401, detail=response.message)
    return response.dict()


@app.post("/api/auth/logout")
async def logout(token: str = Depends(_extract_token)):
    response = await auth_manager.logout_user(token)
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response.dict()


@app.get("/api/users/me")
async def get_current(token_user: User = Depends(get_current_user)):
    return token_user.to_dict()


@app.get("/api/users/{user_id}")
async def get_user(user_id: str, token_user: User = Depends(get_current_user)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@app.get("/api/users/search")
async def search_users(
    q: str,
    limit: int = 20,
    token_user: User = Depends(get_current_user),
):
    results = await contact_service.search_users(q, str(token_user.id), limit)
    return {"users": results}


@app.get("/api/conversations")
async def get_conversations(token_user: User = Depends(get_current_user)):
    conversations = await chat_service.get_user_conversations(str(token_user.id))
    return {"conversations": conversations}


@app.post("/api/conversations/direct")
async def create_direct_chat(
    data: DirectChatRequest, token_user: User = Depends(get_current_user)
):
    conversation = await chat_service.create_direct_conversation(
        str(token_user.id), data.other_user_id
    )
    if not conversation:
        raise HTTPException(status_code=400, detail="Failed to create direct chat")
    return conversation.to_dict()


@app.post("/api/conversations/group")
async def create_group_chat(
    data: GroupChatRequest, token_user: User = Depends(get_current_user)
):
    conversation = await chat_service.create_group_conversation(
        str(token_user.id),
        data.name,
        data.description,
        data.participant_ids,
    )
    if not conversation:
        raise HTTPException(status_code=400, detail="Failed to create group")
    return conversation.to_dict()


@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    token_user: User = Depends(get_current_user),
):
    messages = await chat_service.get_conversation_messages(
        conversation_id, limit, offset
    )
    result = []
    for message in messages:
        msg = message.to_dict()
        if message.sender_id:
            sender = await User.get(message.sender_id.id)
            msg["sender"] = sender.to_dict() if sender else None
        result.append(msg)
    return {"messages": result}


@app.get("/api/conversations/{conversation_id}/participants")
async def get_participants(
    conversation_id: str, token_user: User = Depends(get_current_user)
):
    participants = await chat_service.get_conversation_participants(conversation_id)
    return {"participants": participants}


@app.get("/api/conversations/{conversation_id}/history")
async def get_history(
    conversation_id: str,
    limit: int = 50,
    before: str | None = None,
    token_user: User = Depends(get_current_user),
):
    messages = await message_history_service.get_conversation_messages(
        conversation_id, str(token_user.id), limit, before
    )
    return {"messages": messages}


@app.get("/api/conversations/{conversation_id}/search")
async def search_messages(
    conversation_id: str,
    q: str,
    limit: int = 20,
    token_user: User = Depends(get_current_user),
):
    messages = await message_history_service.search_messages(
        conversation_id, str(token_user.id), q, limit
    )
    return {"messages": messages}


@app.get("/api/conversations/{conversation_id}/stats")
async def conversation_stats(
    conversation_id: str, token_user: User = Depends(get_current_user)
):
    stats = await message_history_service.get_conversation_stats(
        conversation_id, str(token_user.id)
    )
    if not stats:
        raise HTTPException(
            status_code=404, detail="Conversation not found or access denied"
        )
    return stats


@app.get("/api/contacts")
async def get_contacts(token_user: User = Depends(get_current_user)):
    contacts = await contact_service.get_user_contacts(str(token_user.id))
    return {"contacts": contacts}


@app.post("/api/contacts/request")
async def send_contact_request(
    data: dict[str, Any],
    token_user: User = Depends(get_current_user),
):
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    contact = await contact_service.send_contact_request(str(token_user.id), user_id)
    if not contact:
        raise HTTPException(status_code=400, detail="Failed to send contact request")
    return contact.to_dict()


@app.post("/api/contacts/accept")
async def accept_contact(
    data: ContactIdRequest, token_user: User = Depends(get_current_user)
):
    success = await contact_service.accept_contact_request(
        str(token_user.id), data.contact_id
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to accept contact request")
    return {"success": True}


@app.post("/api/contacts/decline")
async def decline_contact(
    data: ContactIdRequest, token_user: User = Depends(get_current_user)
):
    success = await contact_service.decline_contact_request(
        str(token_user.id), data.contact_id
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to decline contact request")
    return {"success": True}


@app.delete("/api/contacts/{contact_user_id}")
async def remove_contact(
    contact_user_id: str, token_user: User = Depends(get_current_user)
):
    success = await contact_service.remove_contact(str(token_user.id), contact_user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove contact")
    return {"success": True}


@app.post("/api/contacts/block")
async def block_user(data: UserIdRequest, token_user: User = Depends(get_current_user)):
    success = await contact_service.block_user(str(token_user.id), data.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to block user")
    return {"success": True}


@app.post("/api/contacts/unblock")
async def unblock_user(
    data: UserIdRequest, token_user: User = Depends(get_current_user)
):
    success = await contact_service.unblock_user(str(token_user.id), data.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unblock user")
    return {"success": True}


@app.get("/api/contacts/pending")
async def get_pending(token_user: User = Depends(get_current_user)):
    return await contact_service.get_pending_requests(str(token_user.id))


@app.get("/api/contacts/blocked")
async def get_blocked(token_user: User = Depends(get_current_user)):
    blocked = await contact_service.get_blocked_users(str(token_user.id))
    return {"blocked_users": blocked}


@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...), token_user: User = Depends(get_current_user)
):
    data = await file.read()
    attachment = await file_service.save_file(
        data,
        file.filename,
        file.content_type or "application/octet-stream",
        str(token_user.id),
    )
    if not attachment:
        raise HTTPException(status_code=400, detail="Failed to save file")
    return {
        "file_id": str(attachment.id),
        "filename": attachment.filename,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
    }


@app.get("/api/files/{file_id}")
async def get_file(file_id: str, token_user: User = Depends(get_current_user)):
    attachment = await file_service.get_file(file_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="File not found")
    file_data = await file_service.get_file_data(attachment.file_path)
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found")
    return Response(
        content=file_data,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"'
        },
    )


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str, token_user: User = Depends(get_current_user)):
    success = await file_service.delete_file(file_id, str(token_user.id))
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete file")
    return {"message": "File deleted successfully"}


@app.get("/api/info")
async def info() -> dict[str, str]:
    return {"name": "Chat API", "version": "1.0.0", "websocket_url": config.ws_url}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
