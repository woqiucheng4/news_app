"""
通知 API
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user_id, get_db
from services.notification import NotificationService

router = APIRouter()


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    notification_type: str
    is_read: bool
    created_at: str


class RegisterPushTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    platform: str = Field(pattern=r"^(ios|android|web)$")
    device_id: Optional[str] = Field(default=None, max_length=255)


@router.post("/register")
async def register_push_token(
    body: RegisterPushTokenRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Register or refresh an FCM device token for the current user."""
    service = NotificationService(db)
    await service.register_push_token(
        user_id=user_id,
        token=body.token,
        platform=body.platform,
        device_id=body.device_id,
    )
    await db.commit()
    return {"success": True}


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 50,
    is_read: Optional[bool] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get in-app notifications for the current user."""
    service = NotificationService(db)
    rows = await service.get_user_notifications(
        user_id,
        is_read=is_read,
        limit=limit,
    )
    return rows


@router.get("/unread-count")
async def get_unread_count(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count."""
    service = NotificationService(db)
    count = await service.get_unread_count(user_id)
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    service = NotificationService(db)
    updated = await service.mark_as_read(notification_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return {"success": True}


@router.put("/read-all")
async def mark_all_as_read(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    service = NotificationService(db)
    updated = await service.mark_all_as_read(user_id)
    await db.commit()
    return {"success": True, "updated": updated}
