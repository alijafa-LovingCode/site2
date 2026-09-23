from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import ChatMessage, RoleEnum, SenderEnum, User
from app.schemas import ChatMessageCreate, ChatMessageOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _cleanup_old_messages(db: Session) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.chat_retention_hours)
    db.execute(delete(ChatMessage).where(ChatMessage.created_at < cutoff))
    db.commit()


@router.get("/messages", response_model=List[ChatMessageOut])
def get_messages(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _cleanup_old_messages(db)
    messages = db.execute(select(ChatMessage).order_by(ChatMessage.created_at)).scalars().all()
    return [ChatMessageOut(id=m.id, sender=m.sender.value, text=m.text, created_at=m.created_at) for m in messages]


@router.post("/messages", response_model=ChatMessageOut)
def send_message(payload: ChatMessageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _cleanup_old_messages(db)
    sender = SenderEnum.ALI if user.role == RoleEnum.ADMIN else SenderEnum.MEHRSA
    message = ChatMessage(sender=sender, text=payload.text.strip())
    db.add(message)
    db.commit()
    db.refresh(message)
    return ChatMessageOut(id=message.id, sender=message.sender.value, text=message.text, created_at=message.created_at)
