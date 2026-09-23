from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.database import get_db
from app.models import Resource, ResourceTypeEnum, User
from app.schemas import ResourceCreate, ResourceOut, ResourceUpdate
from app.services.activity_log import log_activity

router = APIRouter(prefix="/api/resources", tags=["resources"])


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="لینک منبع نامعتبر است.")


def _resource_to_out(r: Resource) -> ResourceOut:
    return ResourceOut(
        id=r.id,
        title=r.title,
        subject_id=r.subject_id,
        subject_name=r.subject.name if r.subject else None,
        grade=r.grade,
        chapter=r.chapter,
        url=r.url,
        description=r.description,
        resource_type=r.resource_type.value,
        is_downloadable=r.is_downloadable,
    )


@router.get("", response_model=List[ResourceOut])
def list_resources(
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Resource).order_by(Resource.id.desc())
    if subject_id:
        query = query.where(Resource.subject_id == subject_id)
    resources = db.execute(query).scalars().all()
    return [_resource_to_out(r) for r in resources]


@router.post("", response_model=ResourceOut)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    _validate_url(payload.url)
    try:
        resource_type = ResourceTypeEnum(payload.resource_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="نوع منبع نامعتبر است.")

    resource = Resource(
        title=payload.title,
        subject_id=payload.subject_id,
        grade=payload.grade,
        chapter=payload.chapter,
        url=payload.url,
        description=payload.description,
        resource_type=resource_type,
        is_downloadable=payload.is_downloadable,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    log_activity(db, admin, "resource_created", details=resource.title)
    return _resource_to_out(resource)


@router.put("/{resource_id}", response_model=ResourceOut)
def update_resource(resource_id: int, payload: ResourceUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="منبع پیدا نشد.")

    data = payload.model_dump(exclude_unset=True)
    if "url" in data:
        _validate_url(data["url"])
    if "resource_type" in data:
        try:
            data["resource_type"] = ResourceTypeEnum(data["resource_type"])
        except ValueError:
            raise HTTPException(status_code=400, detail="نوع منبع نامعتبر است.")

    for field, value in data.items():
        setattr(resource, field, value)
    db.commit()
    db.refresh(resource)
    log_activity(db, admin, "resource_updated", details=resource.title)
    return _resource_to_out(resource)


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="منبع پیدا نشد.")
    db.delete(resource)
    db.commit()
    log_activity(db, admin, "resource_deleted", details=resource.title)
    return {"message": "منبع حذف شد."}
