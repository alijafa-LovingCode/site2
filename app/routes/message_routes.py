from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.database import get_db
from app.models import DailyMessage, MessageCategoryEnum, User
from app.schemas import DailyMessageCreate, DailyMessageOut, DailyMessageUpdate
from app.services.activity_log import log_activity
from app.services.jalali import today_local
from app.services.messages_seed import get_message_for_date

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/today")
def today_message(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = today_local()
    msg = get_message_for_date(db, today)
    if not msg:
        return {"text": None, "category": None}
    return {"text": msg.text, "category": msg.category.value}


@router.get("", response_model=List[DailyMessageOut])
def list_messages(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    messages = db.execute(select(DailyMessage).order_by(DailyMessage.id)).scalars().all()
    return messages


@router.post("", response_model=DailyMessageOut)
def create_message(payload: DailyMessageCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        category = MessageCategoryEnum(payload.category)
    except ValueError:
        raise HTTPException(status_code=400, detail="دسته‌بندی نامعتبر است.")
    msg = DailyMessage(text=payload.text, category=category, is_enabled=payload.is_enabled)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    log_activity(db, admin, "daily_message_created")
    return msg


@router.put("/{message_id}", response_model=DailyMessageOut)
def update_message(message_id: int, payload: DailyMessageUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    msg = db.get(DailyMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="پیام پیدا نشد.")
    data = payload.model_dump(exclude_unset=True)
    if "category" in data:
        try:
            data["category"] = MessageCategoryEnum(data["category"])
        except ValueError:
            raise HTTPException(status_code=400, detail="دسته‌بندی نامعتبر است.")
    for field, value in data.items():
        setattr(msg, field, value)
    db.commit()
    db.refresh(msg)
    log_activity(db, admin, "daily_message_updated")
    return msg


@router.delete("/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    msg = db.get(DailyMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="پیام پیدا نشد.")
    db.delete(msg)
    db.commit()
    log_activity(db, admin, "daily_message_deleted")
    return {"message": "حذف شد."}
