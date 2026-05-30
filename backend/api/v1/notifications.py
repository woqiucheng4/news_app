"""
通知 API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    notification_type: str
    is_read: bool
    created_at: str


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 50,
    is_read: bool = None,
):
    """获取通知列表"""
    # TODO: 实现通知服务
    return []


@router.get("/unread-count")
async def get_unread_count():
    """获取未读通知数量"""
    # TODO: 实现通知服务
    return {"count": 0}


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """标记通知为已读"""
    # TODO: 实现通知服务
    return {"success": True}


@router.put("/read-all")
async def mark_all_as_read():
    """标记所有通知为已读"""
    # TODO: 实现通知服务
    return {"success": True}
